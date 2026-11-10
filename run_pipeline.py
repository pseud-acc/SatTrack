"""SatTrack pipeline entrypoint: ingest -> dbt (tracking, enrichment) -> publish/swap -> audit -> health page -> data summary -> app csv.

Fail-closed in two swap units (plan section 15.2):
  * the run builds into a copy of the live DuckDB file;
  * each unit's marts are kept from the previous live file when that unit fails;
  * the copy is renamed over the live file only at the end, so the app never sees a half build.
Operations data (Elementary + audit) lives in the permanent ops DB, attached by dbt.

Local-run guard: once the scheduled remote run is live, create an empty file named `remote_live` in the
data dir. A run outside GitHub Actions then refuses to start (exit 3) unless --allow-local (or
SATTRACK_ALLOW_LOCAL=1) is given, so a laptop run can't spend the Space-Track quota by accident.

Quiet mode (--quiet or SATTRACK_QUIET=1): one summary line instead of the stage JSON, and the report
scripts' stdout is dropped (their errors still reach stderr).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "ingestion"))

from sattrack_ingest import audit, extractors  # noqa: E402
from sattrack_ingest.config import BUILD_DB, DATA_DIR, LIVE_DB, OPS_DB, WAREHOUSE_DIR, RunContext, connect  # noqa: E402
from sattrack_ingest.raw_writer import prune_history  # noqa: E402

TRANSFORM = ROOT / "transform"
DBT = os.environ.get("SATTRACK_DBT_BIN", "dbt")
UNITS = {"tracking": ["marts_tracking"], "enrichment": ["marts"]}   # unit -> schemas it publishes
REMOTE_LIVE_MARKER = DATA_DIR / "remote_live"
EXIT_LOCAL_BLOCKED = 3


def local_run_blocked(allow_local: bool) -> bool:
    """True when this is a local run and the remote run has been marked live."""
    remote = os.environ.get("GITHUB_ACTIONS") == "true"
    return not remote and not allow_local and REMOTE_LIVE_MARKER.exists()


def run_report(cmd: list[str], quiet: bool, env: dict | None = None) -> int:
    """Run a report script that must never fail the run; returns its exit code (-1 if it couldn't start)."""
    try:
        return subprocess.run(cmd, env=env, check=False, stdout=subprocess.DEVNULL if quiet else None).returncode
    except Exception as exc:  # noqa: BLE001
        print(f"{Path(cmd[1]).stem}: FAILED to start - {type(exc).__name__}", file=sys.stderr)
        return -1


def now() -> datetime:
    return datetime.now(timezone.utc)


def dbt_build(unit: str, run_id: str) -> dict:
    env = dict(os.environ, SATTRACK_DB_PATH=str(BUILD_DB), SATTRACK_OPS_PATH=str(OPS_DB), SATTRACK_RUN_ID=run_id)
    target = TRANSFORM / "target" / unit
    t0 = time.time()
    # buildable: a test runs only when all its parents are built (or upstream), so tests that span both
    # units run with the downstream unit, never against a half-refreshed pair (phase 0 finding).
    proc = subprocess.run([DBT, "build", "--selector", unit, "--indirect-selection", "buildable",
                           "--target-path", str(target), "--profiles-dir", str(TRANSFORM)],
                          cwd=TRANSFORM, env=env, capture_output=True, text=True)
    res_path = target / "run_results.json"
    results = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else None
    statuses = {}
    for r in (results or {}).get("results", []):
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    failed = proc.returncode != 0 or any(s in statuses for s in ("error", "fail", "runtime error"))
    return {"unit": unit, "exit_code": proc.returncode, "duration_s": round(time.time() - t0, 1), "statuses": statuses,
            "failed": failed, "invocation_id": (results or {}).get("metadata", {}).get("invocation_id"),
            "results": results, "log_tail": audit.scrub(proc.stdout[-3000:] + proc.stderr[-1000:])}


def restore_unit_from_live(unit: str) -> bool:
    """Copy the unit's published schemas from the live DB into the build DB. Returns False if no live DB."""
    if not LIVE_DB.exists():
        return False
    with connect(BUILD_DB) as con:
        con.execute(f"attach '{LIVE_DB.as_posix()}' as live (read_only)")
        for schema in UNITS[unit]:
            tables = con.execute("select table_name from duckdb_tables() where database_name = 'live' and schema_name = ?", [schema]).fetchall()
            con.execute(f"create schema if not exists {schema}")
            for (t,) in tables:
                con.execute(f'create or replace table {schema}."{t}" as select * from live.{schema}."{t}"')
        con.execute("detach live")
    return True


MANAGED_SCHEMAS = ("staging", "intermediate", "marts", "marts_tracking")
RAW_SCHEMA_PREFIX = "raw_"


def drop_orphans() -> list[str]:
    """Drop objects of the build DB that nothing in the current project owns:
      * tables/views in dbt-managed schemas that no current model builds;
      * tables in raw_* schemas that no source declares (retired ingests), then any raw_* schema left empty.
    The ops DB and test-failure tables are never touched. Skipped (returns []) if a unit's manifest is
    missing or declares no models or sources, so a missing manifest can never delete anything."""
    owned, declared = set(), set()
    for unit in UNITS:
        mpath = TRANSFORM / "target" / unit / "manifest.json"
        if not mpath.exists():
            return []
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        for node in manifest.get("nodes", {}).values():
            if node.get("resource_type") == "model" and node.get("package_name") == "sattrack":
                owned.add((node.get("schema"), node.get("alias") or node.get("name")))
        for src in manifest.get("sources", {}).values():
            if src.get("package_name") == "sattrack":
                declared.add((src.get("schema"), src.get("identifier") or src.get("name")))
    if not owned or not declared:
        return []
    dropped = []
    with connect(BUILD_DB) as con:
        objs = con.execute(
            "select schema_name, table_name, 'table' from duckdb_tables() where database_name = current_database() "
            "union all select schema_name, view_name, 'view' from duckdb_views() where not internal and database_name = current_database()"
        ).fetchall()
        for schema, name, kind in objs:
            orphan_model = schema in MANAGED_SCHEMAS and (schema, name) not in owned
            orphan_raw = schema.startswith(RAW_SCHEMA_PREFIX) and (schema, name) not in declared
            if orphan_model or orphan_raw:
                con.execute(f'drop {kind} if exists {schema}."{name}"')
                dropped.append(f"{schema}.{name}")
        empty_raw = con.execute(
            "select s.schema_name from duckdb_schemas() as s where s.database_name = current_database() "
            "and s.schema_name like 'raw\\_%' escape '\\' "
            "and not exists (select 1 from duckdb_tables() as t where t.database_name = s.database_name and t.schema_name = s.schema_name) "
            "and not exists (select 1 from duckdb_views() as v where v.database_name = s.database_name and v.schema_name = s.schema_name)"
        ).fetchall()
        for (schema,) in empty_raw:
            con.execute(f'drop schema if exists "{schema}"')
            dropped.append(f"{schema} (schema)")
    return dropped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quiet", action="store_true", default=os.environ.get("SATTRACK_QUIET") == "1",
                    help="print one summary line instead of the stage JSON")
    ap.add_argument("--allow-local", action="store_true", default=os.environ.get("SATTRACK_ALLOW_LOCAL") == "1",
                    help="run locally even though the remote run is marked live")
    args = ap.parse_args()
    if local_run_blocked(args.allow_local):
        print(f"Local run refused: the remote run is live ({REMOTE_LIVE_MARKER} exists). "
              "Use --allow-local (or SATTRACK_ALLOW_LOCAL=1) to run anyway.", file=sys.stderr)
        return EXIT_LOCAL_BLOCKED

    started = now()
    ctx = RunContext(run_id="run_" + started.strftime("%Y-%m-%dT%H%M%SZ"), loaded_at=started.isoformat())
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    stages: list[dict] = []

    # 1. working copy of the live DB
    BUILD_DB.unlink(missing_ok=True)
    if LIVE_DB.exists():
        shutil.copyfile(LIVE_DB, BUILD_DB)

    # 2. ingestion (each source group independent; a failure holds only the unit that depends on it)
    unit_inputs_ok = {"tracking": True, "enrichment": True}
    with connect(BUILD_DB) as con, audit.ops() as ops:
        for name, fn, units in [("spacetrack", extractors.ingest_spacetrack, ["tracking", "enrichment"]),
                                ("gcat", extractors.ingest_gcat, ["enrichment"]),
                                ("pycountry", extractors.ingest_pycountry, ["enrichment"]),
                                ("geonames", extractors.ingest_geonames, ["enrichment"])]:
            t0 = time.time()
            try:
                rows = fn(con, ops, ctx)
                stages.append({"stage": f"ingest:{name}", "status": "ok", "duration_s": round(time.time() - t0, 1), "rows": rows})
            except Exception as exc:  # noqa: BLE001 - recorded, then the dependent unit is held
                stages.append({"stage": f"ingest:{name}", "status": "error", "duration_s": round(time.time() - t0, 1),
                               "error": audit.scrub(f"{type(exc).__name__}: {exc}")})
                for u in units:
                    unit_inputs_ok[u] = False
        removed = prune_history()
        stages.append({"stage": "raw_history_prune", "status": "ok", "removed": removed})

    # 2b. source freshness (warn-only, never blocks: D10)
    env = dict(os.environ, SATTRACK_DB_PATH=str(BUILD_DB), SATTRACK_OPS_PATH=str(OPS_DB))
    ftarget = TRANSFORM / "target" / "freshness"
    subprocess.run([DBT, "source", "freshness", "--target-path", str(ftarget), "--profiles-dir", str(TRANSFORM)],
                   cwd=TRANSFORM, env=env, capture_output=True, text=True)
    fpath = ftarget / "sources.json"
    fresh = json.loads(fpath.read_text(encoding="utf-8")).get("results", []) if fpath.exists() else []
    with audit.ops() as ops:
        for f in fresh:
            crit = (f.get("criteria") or {}).get("warn_after") or {}
            ops.execute("insert into audit.source_freshness values (?, ?, ?, ?, ?, ?)",
                        [ctx.run_id, f.get("unique_id", "").replace("source.sattrack.", ""), f.get("max_loaded_at"),
                         f.get("max_loaded_at_time_ago_in_s"), f.get("status"), f"{crit.get('count')} {crit.get('period')}"])
    stages.append({"stage": "source_freshness", "status": "ok" if all(str(f.get("status")).lower() == "pass" for f in fresh) else "warn",
                   "sources": len(fresh)})

    # 3. dbt, one unit at a time (connections above are closed: DuckDB allows one writer process)
    unit_status = {}
    for unit in ["tracking", "enrichment"]:
        # enrichment is built on the tracking (GP) data, so it is held whenever tracking didn't pass;
        # the reverse never applies (GCAT problems must not block positions).
        if unit == "enrichment" and unit_status.get("tracking") != "ok" and LIVE_DB.exists():
            unit_status[unit] = "held"
            stages.append({"stage": f"dbt:{unit}", "status": "skipped", "reason": "tracking did not pass"})
            continue
        if not unit_inputs_ok[unit] and LIVE_DB.exists():
            unit_status[unit] = "held"
            stages.append({"stage": f"dbt:{unit}", "status": "skipped", "reason": "input ingestion failed"})
            continue
        res = dbt_build(unit, ctx.run_id)
        unit_status[unit] = "error" if res["failed"] else "ok"
        stages.append({"stage": f"dbt:{unit}", "status": unit_status[unit], "duration_s": res["duration_s"],
                       "statuses": res["statuses"], "exit_code": res["exit_code"]})
        with audit.ops() as ops:
            recorded = False
            if res["invocation_id"]:
                try:
                    recorded = ops.execute("select count(*) from main_elementary.dbt_invocations where invocation_id = ?",
                                           [res["invocation_id"]]).fetchone()[0] > 0
                except duckdb.Error:
                    recorded = False
            ops.execute("insert into audit.dbt_crash_capture (run_id, unit, exit_code, flag_elementary_recorded, results) "
                        "values (?, ?, ?, ?, ?)",
                        [ctx.run_id, unit, res["exit_code"], int(recorded),
                         None if recorded else audit.json_dumps({"results": res["results"], "log_tail": res["log_tail"]})])

    # 4. publish: keep the last good version of any unit that didn't pass
    for unit, st in unit_status.items():
        if st != "ok":
            kept = restore_unit_from_live(unit)
            unit_status[unit] = "held" if kept else "error"
            stages.append({"stage": f"publish:{unit}", "status": unit_status[unit],
                           "detail": "kept last good build" if kept else "no previous build to keep"})
        else:
            stages.append({"stage": f"publish:{unit}", "status": "ok", "detail": "published this run"})

    # 4b. drop orphans: dbt never drops tables of renamed/removed models (phase 0 finding)
    dropped = drop_orphans()
    stages.append({"stage": "orphan_cleanup", "status": "ok", "dropped": dropped})

    # 5. swap the whole file into place, then snapshot row counts
    os.replace(BUILD_DB, LIVE_DB)
    stages.append({"stage": "swap", "status": "ok", "detail": "renamed build DB over live DB"})
    with connect(LIVE_DB, read_only=True) as live:
        snap = live.execute("select schema_name, table_name, estimated_size from duckdb_tables() where schema_name in ('marts', 'marts_tracking', 'intermediate', 'staging')").fetchall()
        counts = [(s, t, live.execute(f'select count(*) from {s}."{t}"').fetchone()[0]) for s, t, _ in snap]
    finished = now()
    overall = "ok" if all(v == "ok" for v in unit_status.values()) and all(s.get("status") in ("ok", "skipped") for s in stages) else \
              ("error" if all(v != "ok" for v in unit_status.values()) else "warn")
    with audit.ops() as ops:
        for s, t, n in counts:
            ops.execute("insert into audit.table_snapshot values (?, ?, ?, ?, ?)", [ctx.run_id, s, t, n, finished])
        for unit, st in unit_status.items():
            ops.execute("insert into audit.swap_status values (?, ?, ?, ?, ?)",
                        [ctx.run_id, unit, st, finished if st == "ok" else None, None])
        ops.execute("insert into audit.pipeline_run values (?, ?, ?, ?, ?, ?, ?, ?)",
                    [ctx.run_id, started, finished, overall, os.environ.get("SATTRACK_TRIGGER", "manual"),
                     os.environ.get("SATTRACK_GIT_SHA"), audit.json_dumps({"python": sys.version.split()[0], "duckdb": duckdb.__version__}),
                     audit.json_dumps(stages)])
    if not args.quiet:
        print(json.dumps({"run_id": ctx.run_id, "overall": overall, "units": unit_status, "stages": stages}, indent=2, default=str))

    # 6. health page (never fails the run)
    reports = {"health": run_report([sys.executable, str(ROOT / "scripts" / "build_health_page.py")], args.quiet)}

    # 7. data summary dashboard (never fails the run). dbt Charts lives in its own venv, so its Python is
    # named by SATTRACK_REPORTS_PYTHON; without it the step is skipped.
    reports_python = os.environ.get("SATTRACK_REPORTS_PYTHON")
    if reports_python:
        reports["summary"] = run_report([reports_python, str(ROOT / "scripts" / "build_data_summary.py")], args.quiet,
                                        env=dict(os.environ, SATTRACK_DBT_BIN=DBT))
    elif not args.quiet:
        print("data summary: skipped (SATTRACK_REPORTS_PYTHON not set)")

    # 8. app CSV export for the live Dash app (never fails the run; the script keeps the last good files on error
    # and prints "app csv: <dir>" or the error)
    reports["app_csv"] = run_report([sys.executable, str(ROOT / "scripts" / "export_app_csvs.py")], args.quiet)
    if args.quiet:
        units = " ".join(f"{u}={s}" for u, s in unit_status.items())
        rep = " ".join(f"{k}={'ok' if v == 0 else f'exit {v}'}" for k, v in reports.items())
        print(f"{ctx.run_id} overall={overall} {units} | reports: {rep}")
    return 0 if overall != "error" else 1


if __name__ == "__main__":
    sys.exit(main())

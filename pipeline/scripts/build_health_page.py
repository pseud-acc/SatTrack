"""Build the pipeline health page (plan section 16.3) from the ops DB (Elementary + audit) and the live DB.

Writes data/health/health.json and a self-contained data/health/health.html. Never raises into the
pipeline: on any error it writes a minimal page saying what failed.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from sattrack_ingest.audit import scrub  # noqa: E402
from sattrack_ingest.config import DATA_DIR, LIVE_DB, OPS_DB, connect  # noqa: E402

OUT = DATA_DIR / "health"


def rows(con, sql, params=None):
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _open_ops():
    """In-memory connection with the ops DB attached AS ops (the alias dbt uses), so Elementary's
    views, which reference ops.elementary.*, resolve outside dbt."""
    import duckdb
    con = duckdb.connect()
    con.execute(f"attach '{OPS_DB.as_posix()}' as ops (read_only)")
    con.execute("use ops")
    return con


def collect() -> dict:
    with _open_ops() as ops:
        runs = rows(ops, "select * from audit.pipeline_run order by started_at desc limit 14")
        if not runs:
            return {"error": "No pipeline runs recorded yet."}
        run = runs[0]
        rid, started = run["run_id"], run["started_at"]
        data = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run": {k: run[k] for k in ("run_id", "started_at", "finished_at", "status", "trigger", "git_sha")},
            "versions": json.loads(run["versions"] or "{}"),
            "stages": json.loads(run["stages"] or "[]"),
            "history": [{"run_id": r["run_id"], "started_at": r["started_at"], "status": r["status"]} for r in runs],
            # One row per source table: what this run did, plus the last real fetch, so a run that
            # skipped everything as fresh still shows rows, size, HTTP status and when it was fetched.
            "ingestion": rows(ops, """
                with this_run as (
                    select target_table, source, flag_skipped_fresh, error from audit.ingestion_call
                    where run_id = ? and target_table <> '(login)'
                ),
                last_fetch as (
                    select * from audit.ingestion_call
                    where flag_skipped_fresh = 0 and target_table <> '(login)'
                    qualify row_number() over (partition by target_table order by started_at desc) = 1
                )
                select t.source, t.target_table,
                       case when t.error is not null then 'error' when t.flag_skipped_fresh = 1 then 'skipped (fresh)' else 'fetched' end as this_run,
                       strftime(f.started_at, '%Y-%m-%d %H:%M') as last_fetched_utc,
                       round(date_diff('second', f.started_at, now()::timestamp) / 3600.0, 1) as age_h,
                       f.http_status, f.rows, round(f.bytes / 1048576.0, 1) as mb, round(f.duration_s, 1) as duration_s,
                       f.retries, coalesce(t.error, f.error) as error
                from this_run t left join last_fetch f using (target_table)
                order by t.source, t.target_table""", [rid]),
            "login": rows(ops, "select service, consecutive_failures, last_failure_at, last_success_at from audit.login_state"),
            "units": rows(ops, "select unit, status, as_of from audit.swap_status where run_id = ?", [rid]),
            "freshness": rows(ops, "select source_table, max_loaded_at, round(age_s / 3600, 1) as age_h, status, warn_after "
                                   "from audit.source_freshness where run_id = ? order by source_table", [rid]),
            "tables": rows(ops, """
                with cur as (select * from audit.table_snapshot where run_id = ?),
                     prev as (select * from audit.table_snapshot where run_id = (
                         select run_id from audit.pipeline_run where started_at < ? order by started_at desc limit 1))
                select cur.table_schema, cur.table_name, cur.row_count, prev.row_count as prev_row_count
                from cur left join prev using (table_schema, table_name)
                where cur.table_schema in ('marts', 'marts_tracking') order by 1, 2""", [rid, started]),
        }
        try:
            data["tests"] = rows(ops, """
                select test_short_name as name, coalesce(test_alias, test_short_name) as alias, table_name, column_name,
                       status, failures, severity, test_type, test_sub_type, detected_at,
                       left(test_results_description, 300) as description
                from elementary.elementary_test_results
                where detected_at >= ?
                qualify row_number() over (partition by test_unique_id order by detected_at desc) = 1
                order by case status when 'error' then 0 when 'fail' then 0 when 'warn' then 1 else 2 end, name""", [started])
        except Exception as exc:  # noqa: BLE001 - Elementary schema missing on a first run
            data["tests"] = []
            data["tests_error"] = scrub(str(exc))
        try:
            data["node_errors"] = rows(ops, """
                select name, resource_type, status, left(message, 300) as message, generated_at
                from elementary.dbt_run_results
                where generated_at >= ? and lower(status) not in ('success', 'pass', 'skipped')
                order by generated_at desc""", [str(started)])
        except Exception:  # noqa: BLE001
            data["node_errors"] = []
        try:
            data["models"] = rows(ops, """
                select name, round(execution_time, 2) as execution_time, status, materialization
                from elementary.model_run_results where generated_at >= ?
                qualify row_number() over (partition by unique_id order by generated_at desc) = 1
                order by execution_time desc limit 12""", [str(started)])
        except Exception as exc:  # noqa: BLE001
            data["models"] = []
            data["models_error"] = scrub(str(exc))
    if LIVE_DB.exists():
        with connect(LIVE_DB, read_only=True) as live:
            try:
                data["as_of"] = rows(live, "select max(positions_as_of) as positions_as_of, max(gcat_updated_at) as gcat_updated_at, "
                                           "count(*) as objects, count(*) filter (where operational_status = 'Active') as active "
                                           "from marts.fct__satellite_master")[0]
            except Exception:  # noqa: BLE001
                data["as_of"] = {}
    return data


CSS = """
:root{--bg:#F2F4F7;--surface:#FFF;--surface-2:#E8ECF1;--ink:#16202B;--muted:#5A6677;--line:#D4DBE3;--accent:#1F66AD;
--ok:#24804F;--warn:#A86A10;--crit:#BE3428;--held:#6B4FC0;--skip:#8A94A3;
--f-display:"Saira Condensed","Arial Narrow",sans-serif;--f-body:"Atkinson Hyperlegible","Segoe UI",system-ui,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0E131A;--surface:#151C25;--surface-2:#1C2531;--ink:#E2E8EF;--muted:#93A0B2;--line:#29343F;--accent:#6BAEEE;--ok:#5BC489;--warn:#E3B04E;--crit:#F27C70;--held:#AA8DF2;--skip:#707B8A;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0E131A;--surface:#151C25;--surface-2:#1C2531;--ink:#E2E8EF;--muted:#93A0B2;--line:#29343F;--accent:#6BAEEE;--ok:#5BC489;--warn:#E3B04E;--crit:#F27C70;--held:#AA8DF2;--skip:#707B8A;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.5}
.wrap{max-width:1240px;margin:0 auto;padding-inline:20px;padding-block:28px 64px;display:grid;gap:32px}
h1,h2,h3{font-family:var(--f-display);margin:0;line-height:1.1}h1{font-size:36px}h2{font-size:23px;font-weight:600}
code{font-family:var(--f-mono);font-size:.86em}.muted{color:var(--muted)}.eyebrow{font-family:var(--f-mono);font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.pill{display:inline-flex;align-items:center;gap:6px;font-family:var(--f-mono);font-size:11.5px;text-transform:uppercase;padding:2px 8px;border-radius:4px;border:1px solid currentColor;white-space:nowrap}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor}
.s-ok,.s-pass{color:var(--ok)}.s-warn{color:var(--warn)}.s-error,.s-fail,.s-runtime-error{color:var(--crit)}.s-held{color:var(--held)}.s-skip,.s-skipped{color:var(--skip)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}.grid>*{min-width:0}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px 18px;display:grid;gap:8px;align-content:start}
.big{font-family:var(--f-display);font-size:28px;font-weight:700;line-height:1}
.tbl{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-family:var(--f-mono);font-size:11px;text-transform:uppercase;color:var(--muted);background:var(--surface-2);white-space:nowrap}tr:last-child td{border-bottom:0}
td.r{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--f-mono);font-size:.9em}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));background:var(--surface);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.stage{padding:12px 14px;border-right:1px solid var(--line);display:grid;gap:4px;min-width:0}.stage:last-child{border-right:0}
.stage .d{font-size:12.5px;color:var(--muted);overflow-wrap:anywhere}
@media (max-width:520px){.wrap{padding-inline:16px}}
"""


def esc(v) -> str:
    return html.escape("" if v is None else str(v))


def pill(status) -> str:
    s = (status or "skip").lower().replace(" ", "-")
    return f'<span class="pill s-{esc(s)}">{esc(status)}</span>'


def table(rows_, cols, right=()):
    if not rows_:
        return '<p class="muted">Nothing recorded for this run.</p>'
    head = "".join(f'<th class="{"r" if c in right else ""}">{esc(c)}</th>' for c in cols)
    body = ""
    for r in rows_:
        cells = []
        for c in cols:
            v = r.get(c)
            if c in ("status",):
                cells.append(f"<td>{pill(v)}</td>")
            elif c in right:
                cells.append(f'<td class="r">{esc(f"{v:,}" if isinstance(v, int) else v)}</td>')
            else:
                cells.append(f"<td>{esc(v)}</td>")
        body += "<tr>" + "".join(cells) + "</tr>"
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def render(d: dict) -> str:
    if "error" in d:
        return f"<!doctype html><meta charset=utf-8><title>SatTrack Pipeline Health</title><p>{esc(d['error'])}</p>"
    run, units = d["run"], {u["unit"]: u for u in d["units"]}
    counts = {}
    for t in d.get("tests", []):
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    as_of = d.get("as_of", {})
    stages = "".join(
        f'<div class="stage"><span class="eyebrow">{esc(s["stage"])}</span>{pill(s.get("status"))}'
        f'<span class="d">{esc(s.get("duration_s", ""))}{" s" if s.get("duration_s") is not None else ""} '
        f'{esc(s.get("detail") or s.get("reason") or s.get("error") or "")}'
        f'{esc(" · " + json.dumps(s.get("statuses"))) if s.get("statuses") else ""}</span></div>' for s in d["stages"])
    unit_panels = "".join(
        f'<div class="panel"><div style="display:flex;justify-content:space-between;gap:8px"><h3>{esc(n.title())}</h3>{pill(units.get(n, {}).get("status"))}</div>'
        f'<span class="muted">{esc(lbl)}</span><span class="big" style="font-size:20px">{esc(val)}</span></div>'
        for n, lbl, val in [("tracking", "Positions as of", as_of.get("positions_as_of")),
                            ("enrichment", "Details as of", as_of.get("gcat_updated_at"))])
    failing = [t for t in d.get("tests", []) if t["status"] not in ("pass",)]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SatTrack Pipeline Health</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=JetBrains+Mono:wght@400;500&family=Saira+Condensed:wght@600;700&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<header style="display:grid;gap:6px"><span class="eyebrow">SatTrack data pipeline</span><h1>Pipeline health</h1>
<span class="muted">Run <code>{esc(run["run_id"])}</code> · {esc(run["started_at"])} → {esc(run["finished_at"])} · generated {esc(d["generated_at"])}</span></header>
<div class="grid"><div class="panel"><span class="eyebrow">Overall</span><span class="big s-{esc(run["status"])}">{esc(str(run["status"]).upper())}</span>
<span>{esc(counts.get("pass", 0))} tests passed · {esc(counts.get("warn", 0))} warnings · {esc(counts.get("fail", 0) + counts.get("error", 0))} failed</span>
<span class="muted">{esc(as_of.get("objects"))} objects in the app · {esc(as_of.get("active"))} active</span></div>{unit_panels}</div>
<section style="display:grid;gap:12px"><h2>Latest run, end to end</h2><div class="flow">{stages}</div></section>
<section style="display:grid;gap:12px"><h2>Ingestion</h2>{table(d["ingestion"], ["source", "target_table", "this_run", "last_fetched_utc", "age_h", "http_status", "rows", "mb", "duration_s", "retries", "error"], right=("age_h", "http_status", "rows", "mb", "duration_s", "retries"))}
{table(d["login"], ["service", "consecutive_failures", "last_success_at", "last_failure_at"], right=("consecutive_failures",))}</section>
<section style="display:grid;gap:12px"><h2>Models and nodes that errored</h2>{table(d.get("node_errors", []), ["status", "name", "resource_type", "message"])}</section>
<section style="display:grid;gap:12px"><h2>Tests that didn't pass</h2>{table(failing, ["status", "name", "table_name", "column_name", "failures", "severity", "description"], right=("failures",))}
<p class="muted">{esc(len(d.get("tests", [])))} tests recorded by Elementary for this run. {esc(d.get("tests_error", ""))}</p></section>
<section style="display:grid;gap:12px"><h2>Slowest models</h2>{table(d.get("models", []), ["name", "execution_time", "status", "materialization"], right=("execution_time",))}</section>
<section style="display:grid;gap:12px"><h2>Freshness &amp; tables</h2><div class="grid">{table(d["freshness"], ["source_table", "max_loaded_at", "age_h", "warn_after", "status"], right=("age_h",))}
{table(d["tables"], ["table_schema", "table_name", "row_count", "prev_row_count"], right=("row_count", "prev_row_count"))}</div></section>
<section style="display:grid;gap:12px"><h2>Recent runs</h2>{table(d["history"], ["run_id", "started_at", "status"])}</section>
<footer class="muted" style="font-size:12.5px">Generated by <code>scripts/build_health_page.py</code> from <code>sattrack_ops.duckdb</code>. Versions: {esc(json.dumps(d.get("versions")))}. Error text is scrubbed of URLs, tokens and paths.</footer>
</div></body></html>"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        d = collect()
    except Exception as exc:  # noqa: BLE001 - the page must never break the pipeline
        d = {"error": "Health page could not read the ops database: " + (scrub(str(exc)) or "")}
    (OUT / "health.json").write_text(json.dumps(d, default=str, indent=1), encoding="utf-8")
    (OUT / "health.html").write_text(render(d), encoding="utf-8")
    print("health page:", OUT / "health.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())

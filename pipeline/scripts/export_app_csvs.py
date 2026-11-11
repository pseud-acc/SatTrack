"""Export the CSV files the live SatTrack Dash app reads, from the app marts (lift-and-shift).

The queries are dbt analyses in transform/analyses/app_export/ (one per file, documented in
_app_export__analyses.yml); this script holds no query logic. For each analysis it:
  1. reads the .sql file and resolves every {{ ref('<model>') }} to that model's table in the live DB
     (it must be a mart: schema marts or marts_tracking);
  2. runs it on a read-only connection with DuckDB's own COPY ... TO csv (header, ',' delimiter, '"' quote only
     where needed, LF line ends: the old pandas export's format);
  3. checks the written file against the app's column contract (names and order) and that no cell is empty
     (the app drops any row with a missing value), and that the satellite file has at least MIN_SATELLITE_ROWS rows.
Only when every file passes are the temp files renamed over the published ones (os.replace), followed by
manifest.json (file, rows, sha256, generated_at, run id, as-of dates). On any failure nothing is replaced, so the
last good files stay in place.

Output: DATA_DIR/app/<analysis name without "app__">.csv, i.e. satcat_tle.csv and last_data_update.csv.

Why read the analyses directly rather than `dbt compile`: the only Jinja allowed is ref(), which resolves to a
table in the live DB, so no dbt run (and no project-wide parse) is needed at export time. `dbt parse` still sees
the files as analyses, so they appear in the docs and lineage.

Run with the pipeline venv's Python:
  python scripts/export_app_csvs.py                       # live DB -> DATA_DIR/app/
  python scripts/export_app_csvs.py --out <dir> --db <file>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from sattrack_ingest.config import DATA_DIR, LIVE_DB, connect  # noqa: E402

ANALYSES_DIR = ROOT / "transform" / "analyses" / "app_export"
ANALYSES_YML = ANALYSES_DIR / "_app_export__analyses.yml"
PREFIX = "app__"
MART_SCHEMAS = ("marts", "marts_tracking")
MIN_SATELLITE_ROWS = 1000   # the old pipeline's own sanity floor for a catalogue download

# The app's column contract per file: names and order the Dash app reads (SatTrack app/core/state.py and helpers).
APP_COLUMNS = {
    "satcat_tle.csv": [
        "SatCatId", "ObjectName", "LaunchYear", "OrbitalPeriod", "LaunchMass", "StatusCode", "Inclination", "Status",
        "UcsData", "OrbitClassEstimated", "LaunchSiteCountry", "Owner", "UseType", "Purpose", "LaunchVehicleClass",
        "TLE1", "TLE2", "MeanMotion", "Eccentricity", "OrbitClass",
    ],
    "last_data_update.csv": ["Source", "Last Download", "Last Update"],
}
# Columns allowed to hold empty cells (the app never reads them).
NULLABLE = {"last_data_update.csv": {"Last Download"}}

_REF = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*\)\s*\}\}")
_JINJA = re.compile(r"\{\{|\{%|\{#")


class ExportError(Exception):
    pass


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def load_analyses() -> dict[str, str]:
    """{csv file name: raw SQL}, checking each analysis is documented and uses no Jinja other than ref()."""
    files = sorted(ANALYSES_DIR.glob(f"{PREFIX}*.sql"))
    if not files:
        raise ExportError(f"no analyses found in {ANALYSES_DIR}")
    yml = ANALYSES_YML.read_text(encoding="utf-8") if ANALYSES_YML.exists() else ""
    problems, out = [], {}
    for f in files:
        name = f.stem
        csv_name = name.removeprefix(PREFIX) + ".csv"
        sql = f.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        if not re.search(rf"-\s+name:\s+{re.escape(name)}\s*\n\s+description:\s*\S", yml):
            problems.append(f"{name}: no description in {ANALYSES_YML.name}")
        if _JINJA.search(_REF.sub("", sql)):
            problems.append(f"{name}: uses Jinja other than ref()")
        if not _REF.search(sql):
            problems.append(f"{name}: reads no model via ref()")
        if csv_name not in APP_COLUMNS:
            problems.append(f"{name}: {csv_name} is not a file the app reads (no column contract)")
        out[csv_name] = sql
    missing = set(APP_COLUMNS) - set(out)
    if missing:
        problems.append(f"no analysis for {sorted(missing)}")
    if problems:
        raise ExportError("analysis rules broken:\n  " + "\n  ".join(problems))
    return out


def resolve_refs(con, sql: str) -> str:
    """Replace each ref() with the model's table in the live DB; it must exist in exactly one mart schema."""
    def table_for(m: re.Match) -> str:
        model = m.group(1)
        rows = con.execute(
            "select schema_name from duckdb_tables() where database_name = current_database() "
            "and table_name = ? and schema_name in (?, ?)", [model, *MART_SCHEMAS]).fetchall()
        if len(rows) != 1:
            raise ExportError(f"ref('{model}'): expected one mart table, found {len(rows)}")
        return f'"{rows[0][0]}"."{model}"'
    return _REF.sub(table_for, sql)


def check_file(con, path: Path, csv_name: str) -> int:
    """The written file must have the app's columns in order and no empty cell outside NULLABLE. Returns rows."""
    src = f"read_csv('{_sql_path(path)}', header = true, all_varchar = true)"
    cols = [r[0] for r in con.execute(f"select column_name from (describe select * from {src})").fetchall()]
    if cols != APP_COLUMNS[csv_name]:
        raise ExportError(f"{csv_name}: columns {cols} do not match the app's {APP_COLUMNS[csv_name]}")
    required = [c for c in cols if c not in NULLABLE.get(csv_name, set())]
    empty = " or ".join(f'"{c}" is null' for c in required)
    rows, bad = con.execute(f"select count(*), count(*) filter (where {empty}) from {src}").fetchone()
    if bad:
        raise ExportError(f"{csv_name}: {bad} rows have an empty cell (the app would drop them)")
    if csv_name == "satcat_tle.csv" and rows < MIN_SATELLITE_ROWS:
        raise ExportError(f"{csv_name}: only {rows} rows (< {MIN_SATELLITE_ROWS})")
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iso(ts) -> str | None:
    return ts.isoformat() if ts else None


def export(out_dir: Path, db: Path) -> Path:
    analyses = load_analyses()
    out_dir.mkdir(parents=True, exist_ok=True)
    temps: dict[str, Path] = {}
    files = []
    try:
        with connect(db, read_only=True) as con:
            for csv_name, raw in analyses.items():
                sql = resolve_refs(con, raw)
                tmp = out_dir / f".{csv_name}.tmp"
                temps[csv_name] = tmp
                con.execute(f"copy ({sql}) to '{_sql_path(tmp)}' "
                            "(format csv, header true, delimiter ',', quote '\"', new_line '\\n')")
                rows = check_file(con, tmp, csv_name)
                files.append({"file": csv_name, "rows": rows, "sha256": sha256(tmp),
                              "analysis": f"transform/analyses/app_export/{PREFIX}{csv_name.removesuffix('.csv')}.sql"})
            mart = resolve_refs(con, "{{ ref('fct__satellite_master') }}")
            as_of = con.execute(f"""
                select
                    max(positions_as_of) as positions_as_of
                    , max(gcat_updated_at) as gcat_updated_at
                    , max(inserted_by) as run_id
                    , max(inserted_date_time) as mart_built_at
                from {mart}
            """).fetchone()
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_db": db.name,
            "run_id": as_of[2],
            "mart_built_at": _iso(as_of[3]),
            "positions_as_of": _iso(as_of[0]),
            "gcat_updated_at": _iso(as_of[1]),
            "files": files,
        }
        mtmp = out_dir / ".manifest.json.tmp"
        temps["manifest.json"] = mtmp
        mtmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        # every file passed: publish (the CSVs first, then the manifest that describes them)
        for name, tmp in temps.items():
            os.replace(tmp, out_dir / name)
        temps.clear()
        return out_dir
    finally:
        for tmp in temps.values():   # failure: drop temp files, keep the last good published ones
            tmp.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DATA_DIR / "app", help="output directory (default DATA_DIR/app)")
    ap.add_argument("--db", type=Path, default=LIVE_DB, help="DuckDB file to read, read-only (default the live DB)")
    args = ap.parse_args()
    try:
        print(f"app csv: {export(args.out, args.db)}")
        return 0
    except Exception as exc:  # noqa: BLE001 - reported; the last good files are kept
        print(f"app csv: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

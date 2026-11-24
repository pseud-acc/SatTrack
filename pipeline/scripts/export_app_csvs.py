"""Export the files the SatTrack app reads, from the app marts: the CSVs the Dash app loads today and the JSON
datasets the browser loads (docs/app-data-contract.md; decisions D-009 to D-012).

The queries are dbt analyses in transform/analyses/app_export/ (one per file, documented in
_app_export__analyses.yml); this script holds no query logic. For each analysis it:
  1. reads the .sql file and resolves every {{ ref('<model>') }} to that model's table in the live DB
     (it must be a mart: schema marts or marts_tracking);
  2. runs it on a read-only connection with DuckDB's own COPY ... TO csv (header, ',' delimiter, '"' quote only
     where needed, LF line ends: the old pandas export's format);
  3. checks the written file against the app's column contract (names and order) and that no cell is empty
     (the app drops any row with a missing value), and that the satellite file has at least MIN_SATELLITE_ROWS rows.
A dataset analysis (a name in DATASETS, e.g. app__objects) instead returns one row per record: the rows are
wrapped in the dataset envelope (dataset, schema, count, generated_at, run_id, key, attribution, caution, records),
every record is validated against its JSON Schema in app/contracts/, the count and the key (unique, sorted) are
checked, and the file is written pre-compressed twice: <dataset>.json.br (Brotli) and <dataset>.json.gz (gzip).
Only when every file passes are the temp files renamed over the published ones (os.replace), followed by
manifest.json (file, rows, sha256, generated_at, run id, as-of dates). On any failure nothing is replaced, so the
last good files stay in place.

Output: DATA_DIR/app/: satcat_tle.csv, last_data_update.csv, objects.json.br, objects.json.gz, manifest.json.

Why read the analyses directly rather than `dbt compile`: the only Jinja allowed is ref(), which resolves to a
table in the live DB, so no dbt run (and no project-wide parse) is needed at export time. `dbt parse` still sees
the files as analyses, so they appear in the docs and lineage.

Run with the pipeline venv's Python:
  python scripts/export_app_csvs.py                       # live DB -> DATA_DIR/app/
  python scripts/export_app_csvs.py --out <dir> --db <file>
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import brotli
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))
from sattrack_ingest.config import DATA_DIR, LIVE_DB, connect  # noqa: E402

ANALYSES_DIR = ROOT / "transform" / "analyses" / "app_export"
ANALYSES_YML = ANALYSES_DIR / "_app_export__analyses.yml"
PREFIX = "app__"
MART_SCHEMAS = ("marts", "marts_tracking")
MIN_SATELLITE_ROWS = 1000   # the old pipeline's own sanity floor for a catalogue download
CONTRACTS_DIR = ROOT.parent / "app" / "contracts"   # JSON Schemas of the datasets (the app owns the contract)

# The browser datasets (D-010): analysis app__<name> -> files <name>.json.br and <name>.json.gz, validated against
# app/contracts/<name>.schema.json. schema: the envelope's version (raise it when a field is renamed or changes
# meaning); min_records: a sanity floor like MIN_SATELLITE_ROWS.
DATASETS = {
    "objects": {"schema": 1, "key": "satcat_id", "min_records": MIN_SATELLITE_ROWS},
}
# Carried in every dataset's header (CLAUDE.md: public outputs with Space-Track fields cite the source and keep the
# caution; GCAT is CC BY; CelesTrak's group lists are credited wherever shown, D-026).
ATTRIBUTION = [
    "Orbital data: USSPACECOM via Space-Track.org",
    "Launch, owner and mission details: GCAT (J. McDowell, planet4589.org), CC BY 4.0",
    "Constellation groups: CelesTrak (Dr T.S. Kelso)",
]
CAUTION = "Public element sets must not be used for conjunction (collision) assessment."


def dataset_files(name: str) -> list[str]:
    """The published files of a dataset: Brotli for browsers that accept it, gzip for the rest."""
    return [f"{name}.json.br", f"{name}.json.gz"]

# The app's column contract per file: names and order the Dash app reads (SatTrack app/core/state.py and helpers).
APP_COLUMNS = {
    "satcat_tle.csv": [
        "SatCatId", "ObjectName", "LaunchYear", "OrbitalPeriod", "LaunchMass", "Inclination", "Status",
        "LaunchSiteCountry", "Owner", "UseType", "Purpose", "LaunchVehicleClass",
        "TLE1", "TLE2", "MeanMotion", "Eccentricity", "OrbitClass",
        # OMM elements (plan 1.2): with MeanMotion, Eccentricity and Inclination, a full element set
        "Epoch", "RaOfAscNode", "ArgOfPericenter", "MeanAnomaly", "Bstar", "MeanMotionDot", "MeanMotionDdot",
        "RevAtEpoch", "ElementSetNo", "EphemerisType", "ClassificationType", "ObjectId",
    ],
    "last_data_update.csv": ["Source", "Last Download", "Last Update"],
}
# Columns allowed to hold empty cells: the app never reads Last Download, and reads TLE1/TLE2 only as a fallback
# for a satellite without OMM elements (which the export never writes).
NULLABLE = {"last_data_update.csv": {"Last Download"}, "satcat_tle.csv": {"TLE1", "TLE2"}}

_REF = re.compile(r"\{\{\s*ref\(\s*'([^']+)'\s*\)\s*\}\}")
_JINJA = re.compile(r"\{\{|\{%|\{#")


class ExportError(Exception):
    pass


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def load_analyses() -> dict[str, str]:
    """{csv file name or dataset name: raw SQL}, checking each analysis is documented and uses no Jinja other than
    ref()."""
    files = sorted(ANALYSES_DIR.glob(f"{PREFIX}*.sql"))
    if not files:
        raise ExportError(f"no analyses found in {ANALYSES_DIR}")
    yml = ANALYSES_YML.read_text(encoding="utf-8") if ANALYSES_YML.exists() else ""
    problems, out = [], {}
    for f in files:
        name = f.stem
        stem = name.removeprefix(PREFIX)
        output = stem if stem in DATASETS else stem + ".csv"
        sql = f.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
        if not re.search(rf"-\s+name:\s+{re.escape(name)}\s*\n\s+description:\s*\S", yml):
            problems.append(f"{name}: no description in {ANALYSES_YML.name}")
        if _JINJA.search(_REF.sub("", sql)):
            problems.append(f"{name}: uses Jinja other than ref()")
        if not _REF.search(sql):
            problems.append(f"{name}: reads no model via ref()")
        if output not in APP_COLUMNS and output not in DATASETS:
            problems.append(f"{name}: {output} is not a file the app reads (no column contract or dataset)")
        out[output] = sql
    missing = (set(APP_COLUMNS) | set(DATASETS)) - set(out)
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


def build_dataset(con, sql: str, name: str, run_id: str | None, generated_at: str) -> tuple[bytes, int]:
    """Run a dataset analysis and return (the envelope as UTF-8 JSON, record count) after checking it against the
    contract: every record valid under app/contracts/<name>.schema.json, the key unique and sorted, the count
    above the dataset's floor. Raises ExportError with the first few problems."""
    spec = DATASETS[name]
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    records = [dict(zip(cols, row)) for row in cur.fetchall()]
    envelope = {
        "dataset": name,
        "schema": spec["schema"],
        "count": len(records),
        "generated_at": generated_at,
        "run_id": run_id,
        "key": spec["key"],
        "attribution": ATTRIBUTION,
        "caution": CAUTION,
        "records": records,
    }
    schema = json.loads((CONTRACTS_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(envelope), key=lambda e: list(e.absolute_path))
    if errors:
        shown = [f"{'/'.join(map(str, e.absolute_path)) or '(envelope)'}: {e.message}" for e in errors[:5]]
        raise ExportError(f"{name}: {len(errors)} contract violations, e.g.\n    " + "\n    ".join(shown))
    keys = [r[spec["key"]] for r in records]
    if keys != sorted(set(keys)):
        raise ExportError(f"{name}: {spec['key']} is not unique and sorted")
    if len(records) < spec["min_records"]:
        raise ExportError(f"{name}: only {len(records)} records (< {spec['min_records']})")
    # allow_nan=False: NaN/Infinity are not JSON; the schema's number checks already exclude them
    body = json.dumps(envelope, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return body, len(records)


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
        generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with connect(db, read_only=True) as con:
            # Positions come from the tracking mart, details from the enrichment mart (see app__satcat_tle.sql);
            # each is reported with the run that built it, so a held enrichment unit shows as an older details run.
            tracking = resolve_refs(con, "{{ ref('fct__gp_elements') }}")
            details = resolve_refs(con, "{{ ref('fct__satellite_master') }}")
            pos = con.execute(f"""
                select
                    max(_loaded_at) as positions_as_of
                    , max(inserted_by) as run_id
                    , max(inserted_date_time) as built_at
                from {tracking}
            """).fetchone()
            det = con.execute(f"""
                select
                    max(gcat_updated_at) as gcat_updated_at
                    , max(inserted_by) as run_id
                    , max(inserted_date_time) as built_at
                from {details}
            """).fetchone()
            for output, raw in analyses.items():
                sql = resolve_refs(con, raw)
                analysis = f"transform/analyses/app_export/{PREFIX}{output.removesuffix('.csv')}.sql"
                if output in DATASETS:
                    body, rows = build_dataset(con, sql, output, pos[1], generated_at)
                    encoded = {f"{output}.json.br": brotli.compress(body, quality=11, lgwin=24),
                               f"{output}.json.gz": gzip.compress(body, compresslevel=9, mtime=0)}
                    for file_name, data in encoded.items():
                        tmp = out_dir / f".{file_name}.tmp"
                        temps[file_name] = tmp
                        tmp.write_bytes(data)
                        files.append({"file": file_name, "rows": rows, "sha256": sha256(tmp), "dataset": output,
                                      "schema": DATASETS[output]["schema"], "analysis": analysis})
                    continue
                tmp = out_dir / f".{output}.tmp"
                temps[output] = tmp
                con.execute(f"copy ({sql}) to '{_sql_path(tmp)}' "
                            "(format csv, header true, delimiter ',', quote '\"', new_line '\\n')")
                rows = check_file(con, tmp, output)
                files.append({"file": output, "rows": rows, "sha256": sha256(tmp), "analysis": analysis})
        manifest = {
            "generated_at": generated_at,
            "source_db": db.name,
            "run_id": pos[1],
            "mart_built_at": _iso(pos[2]),
            "positions_as_of": _iso(pos[0]),
            "details_run_id": det[1],
            "details_built_at": _iso(det[2]),
            "gcat_updated_at": _iso(det[0]),
            "files": files,
        }
        mtmp = out_dir / ".manifest.json.tmp"
        temps["manifest.json"] = mtmp
        mtmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        # every file passed: publish (the CSVs and datasets first, then the manifest that describes them)
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
        print(f"app export: {export(args.out, args.db)}")
        return 0
    except Exception as exc:  # noqa: BLE001 - reported; the last good files are kept
        print(f"app export: FAILED - {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

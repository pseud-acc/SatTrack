"""Land source data unchanged: all VARCHAR, original column names, plus metadata columns.

Metadata (plan section 3.2): _loaded_at, _run_id, _source_url, _source_updated_at,
_source_row_number, _source_file. Each load is also copied to Parquet for the raw history (D8).
"""
from __future__ import annotations

import csv
import io
import tempfile
import time
from pathlib import Path

from .config import RAW_HISTORY_DIR, RAW_HISTORY_RETENTION_DAYS, RunContext


def _quote(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def land_delimited(con, ctx: RunContext, schema: str, table: str, text: str, *, delimiter: str,
                   source_url: str, source_updated_at: str | None, source_file: str) -> int:
    """Load delimited text (header row first) into <schema>.<table>, replacing it. Returns row count."""
    con.execute(f"create schema if not exists {schema}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False, newline="") as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    try:
        con.execute(
            f"""
            create or replace table {schema}.{_quote(table)} as
            select src.*,
                   cast(? as varchar) as _loaded_at,
                   cast(? as varchar) as _run_id,
                   cast(? as varchar) as _source_url,
                   cast(? as varchar) as _source_updated_at,
                   cast(row_number() over () as varchar) as _source_row_number,
                   cast(? as varchar) as _source_file
            from read_csv(?, delim = ?, header = true, all_varchar = true, quote = '', escape = '',
                          null_padding = true, ignore_errors = false, sample_size = -1) as src
            """,
            [ctx.loaded_at, ctx.run_id, source_url, source_updated_at, source_file, tmp_path, delimiter],
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    n = con.execute(f"select count(*) from {schema}.{_quote(table)}").fetchone()[0]
    _write_history(con, ctx, schema, table)
    return n


def land_records(con, ctx: RunContext, schema: str, table: str, records: list[dict], *,
                 source_url: str, source_updated_at: str | None, source_file: str) -> int:
    """Load a list of JSON objects (values stringified, keys as columns)."""
    keys: list[str] = []
    for r in records:
        for k in r:
            if k not in keys:
                keys.append(k)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar=None)
    w.writerow(keys)
    for r in records:
        w.writerow(["" if r.get(k) is None else str(r.get(k)).replace("\t", " ").replace("\n", " ") for k in keys])
    return land_delimited(con, ctx, schema, table, buf.getvalue(), delimiter="\t", source_url=source_url,
                          source_updated_at=source_updated_at, source_file=source_file)


def _write_history(con, ctx: RunContext, schema: str, table: str) -> None:
    target = RAW_HISTORY_DIR / schema / table
    target.mkdir(parents=True, exist_ok=True)
    out = target / f"{ctx.run_id.replace(':', '')}.parquet"
    con.execute(f"copy {schema}.{_quote(table)} to '{out.as_posix()}' (format parquet)")


def prune_history() -> int:
    """Delete raw-history files older than the retention window. Returns files removed."""
    cutoff = time.time() - RAW_HISTORY_RETENTION_DAYS * 86400
    removed = 0
    for f in RAW_HISTORY_DIR.rglob("*.parquet"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
    return removed

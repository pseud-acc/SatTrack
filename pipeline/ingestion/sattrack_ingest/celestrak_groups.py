"""CelesTrak constellation and operator groups (D-026), landed raw into raw_celestrak.

Three tables, all VARCHAR plus the usual load metadata (raw_writer.py):
  * group_config     the group list from config.py (group, kind, precedence order); landed every run, no request;
  * gp_group_index   every group CelesTrak's GP index page lists, with its title and position on the page;
  * gp_group_member  the CSV of each configured group CelesTrak lists, unchanged, with the group name in front
                     (column GROUP, CelesTrak's own query parameter).

Download rules (D-008, D-026, CelesTrak usage policy of 2026-11-16, proposed D-039):
  * CSV, gzip, one request per group, a pause between requests, the shared client's stop-on-any-non-200
    (celestrak.py); a refusal stops the fetch at once and is never retried in the run;
  * at most once per CELESTRAK_MIN_HOURS (the landed copy's age), and no request at all for
    CELESTRAK_REFUSAL_COOLDOWN_HOURS after a refusal (recorded in the ops DB, audit.source_refusal);
  * all or nothing: the index and every group must arrive and parse, or nothing is replaced, so the last good copy
    (carried in the warehouse from run to run) stays. A first run with nothing to keep lands empty tables;
  * never raises for a CelesTrak problem and never holds a dbt unit: the stage reports "skipped" with the reason.
    A refusal that lasts shows up as the source's freshness warning after 3 days (D-008's 3-day rule, D-037 email).
"""
from __future__ import annotations

import csv
import io
import time
from datetime import datetime, timezone

from . import audit, celestrak
from .config import (CELESTRAK_CONSTELLATION_GROUPS, CELESTRAK_EXCLUDED_GROUPS, CELESTRAK_MIN_HOURS,
                     CELESTRAK_OPERATOR_GROUPS, CELESTRAK_PAUSE_S, CELESTRAK_REFUSAL_COOLDOWN_HOURS, RunContext)
from .raw_writer import land_records

SCHEMA = "raw_celestrak"
SOURCE = "celestrak"
USER_AGENT = "SatTrack-pipeline/0.1 (+https://github.com/pseud-acc/SatTrack)"
MEMBER_COLUMNS = ("NORAD_CAT_ID", "OBJECT_NAME", "OBJECT_ID")     # what the models read; the rest is kept as is
METADATA = ("_loaded_at", "_run_id", "_source_url", "_source_updated_at", "_source_row_number", "_source_file")
# Columns of the empty tables a first run creates when it has no copy to keep (a real load replaces them).
EMPTY_TABLES = {
    "gp_group_member": ("GROUP",) + MEMBER_COLUMNS,
    "gp_group_index": ("GROUP", "GROUP_TITLE", "INDEX_POSITION"),
}


def included_groups() -> list[tuple[str, str]]:
    """[(group, kind)] in precedence order: constellations first, then operators."""
    return ([(g, "constellation") for g in CELESTRAK_CONSTELLATION_GROUPS]
            + [(g, "operator") for g in CELESTRAK_OPERATOR_GROUPS])


def config_records() -> list[dict]:
    rows = [{"GROUP": g, "GROUP_KIND": kind, "GROUP_ORDER": str(i)} for i, (g, kind) in enumerate(included_groups(), 1)]
    rows += [{"GROUP": g, "GROUP_KIND": "excluded", "GROUP_ORDER": ""} for g in CELESTRAK_EXCLUDED_GROUPS]
    return rows


class LayoutChanged(Exception):
    """CelesTrak answered 200 but the page or file isn't what the parser expects: keep the last copy."""


def parse_index(html: str) -> list[dict]:
    """Index records (GROUP, GROUP_TITLE, INDEX_POSITION) for every group the page links, in page order.
    Raises LayoutChanged when no group is linked or a configured group on the page has no title."""
    listed = celestrak.groups_on_index(html)
    if not listed:
        raise LayoutChanged("no groups linked from the GP index page")
    titles = celestrak.group_titles(html)
    untitled = [g for g, _ in included_groups() if g in listed and not titles.get(g)]
    if untitled:
        raise LayoutChanged(f"no title on the GP index page for {untitled}")
    return [{"GROUP": g, "GROUP_TITLE": titles.get(g, ""), "INDEX_POSITION": str(i)} for i, g in enumerate(listed, 1)]


def not_in_config(listed: list[str]) -> list[str]:
    """Groups the index lists that are neither included nor excluded (the dbt check warns on the same rule)."""
    known = {g for g, _ in included_groups()} | set(CELESTRAK_EXCLUDED_GROUPS)
    return [g for g in listed if g not in known]


def member_records(group: str, body: str) -> tuple[list[str], list[dict]]:
    """(CSV header, the group's rows as records with GROUP first). Raises LayoutChanged on a ragged row."""
    rows = list(csv.reader(io.StringIO(body)))
    header, data = rows[0], [r for r in rows[1:] if r]
    ragged = [i for i, r in enumerate(data, 2) if len(r) != len(header)]
    if ragged:
        raise LayoutChanged(f"{group}: {len(ragged)} rows with a different number of fields")
    return header, [{"GROUP": group, **dict(zip(header, r))} for r in data]


def _table_exists(con, table: str) -> bool:
    return con.execute("select count(*) from duckdb_tables() where schema_name = ? and table_name = ?",
                       [SCHEMA, table]).fetchone()[0] > 0


def ensure_tables(con) -> list[str]:
    """Create any missing raw table empty, so the models build on a first run that got nothing. Returns those made."""
    con.execute(f"create schema if not exists {SCHEMA}")
    made = []
    for table, cols in EMPTY_TABLES.items():
        if not _table_exists(con, table):
            col_sql = ", ".join(f'"{c}" varchar' for c in cols + METADATA)
            con.execute(f"create table {SCHEMA}.{table} ({col_sql})")
            made.append(table)
    return made


def landed_age_hours(con, clock=time.time) -> float | None:
    """Hours since the members were last landed; None when never (or the table is empty)."""
    if not _table_exists(con, "gp_group_member"):
        return None
    latest = con.execute(f"select max(epoch(cast(_loaded_at as timestamptz))) from {SCHEMA}.gp_group_member").fetchone()[0]
    return None if latest is None else (clock() - latest) / 3600.0


def last_refusal(ops) -> tuple[float, int | None] | None:
    """(epoch seconds, HTTP status) of the latest CelesTrak refusal, or None."""
    row = ops.execute("select refused_at_epoch_s, http_status from audit.source_refusal where source = ? "
                      "order by refused_at_epoch_s desc limit 1", [SOURCE]).fetchone()
    return (row[0], row[1]) if row else None


def _record(ops, ctx, table, url, t0, status, size, rows, error, skipped=0):
    audit.record_call(ops, ctx.run_id, source=SOURCE, target_table=f"{SCHEMA}.{table}", url=url,
                      started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                      http_status=status, bytes=size, rows=rows, retries=0, flag_skipped_fresh=skipped, error=error)


def fetch(ops, ctx: RunContext, opener=celestrak._open, sleep=time.sleep) -> tuple[list[dict], list[dict]]:
    """Download the index and the configured groups. Returns (index records, member records).
    Raises celestrak.Refused (stop, recorded by the caller) or LayoutChanged."""
    def get(url, table):
        t0 = time.time()
        try:
            body = celestrak.get(url, opener, user_agent=USER_AGENT)
        except celestrak.Refused as e:
            _record(ops, ctx, table, url, t0, e.status, 0, 0, str(e))
            raise
        return body, t0

    html, t0 = get(celestrak.INDEX_URL, "gp_group_index")
    index = parse_index(html)
    _record(ops, ctx, "gp_group_index", celestrak.INDEX_URL, t0, 200, len(html.encode()), len(index), None)
    listed = [r["GROUP"] for r in index]
    header, members = None, []
    for group, _ in included_groups():
        if group not in listed:          # never request a group the index no longer lists: it would be a 404
            continue
        sleep(CELESTRAK_PAUSE_S)
        url = celestrak.GROUP_URL.format(group=group)
        body, t0 = get(url, "gp_group_member")
        try:
            rows = celestrak.check_csv(body, url, MEMBER_COLUMNS)
        except celestrak.Refused as e:
            _record(ops, ctx, "gp_group_member", url, t0, 200, len(body.encode()), 0, str(e))
            raise
        group_header, records = member_records(group, body)
        if header is not None and group_header != header:
            raise LayoutChanged(f"{group}: CSV columns differ from the other groups'")
        header = group_header
        members += records
        _record(ops, ctx, "gp_group_member", url, t0, 200, len(body.encode()), rows, None)
    if header is None:
        raise LayoutChanged("the index lists none of the configured groups")
    return index, members


def ingest_celestrak_groups(con, ops, ctx: RunContext, opener=celestrak._open, sleep=time.sleep,
                            clock=time.time) -> dict:
    """Land the group config, then (when due) the index and the groups. Never raises for a CelesTrak problem."""
    out: dict = {"group_config": land_records(con, ctx, SCHEMA, "group_config", config_records(),
                                              source_url="sattrack_ingest.config", source_updated_at=None,
                                              source_file="config.py")}
    made = ensure_tables(con)
    if made:
        out["created_empty"] = made
    refusal = last_refusal(ops)
    if refusal and clock() - refusal[0] < CELESTRAK_REFUSAL_COOLDOWN_HOURS * 3600:
        hours = (clock() - refusal[0]) / 3600
        return {**out, "stage_status": "skipped",
                "reason": f"refused {hours:.1f} h ago (HTTP {refusal[1]}); no requests for "
                          f"{CELESTRAK_REFUSAL_COOLDOWN_HOURS} h; kept last copy"}
    age = landed_age_hours(con, clock)
    if age is not None and age < CELESTRAK_MIN_HOURS:
        _record(ops, ctx, "gp_group_member", celestrak.INDEX_URL, time.time(), None, 0, None, None, skipped=1)
        return {**out, "stage_status": "skipped", "reason": f"landed {age:.1f} h ago (limit {CELESTRAK_MIN_HOURS} h)"}
    try:
        index, members = fetch(ops, ctx, opener, sleep)
    except celestrak.Refused as e:
        ops.execute("insert into audit.source_refusal values (?, ?, ?, ?, ?)",
                    [ctx.run_id, SOURCE, clock(), e.status, audit.scrub(str(e))])
        return {**out, "stage_status": "skipped", "reason": f"refused: {audit.scrub(str(e))}; kept last copy"}
    except LayoutChanged as e:
        return {**out, "stage_status": "skipped", "reason": f"layout changed: {e}; kept last copy"}
    con.execute("begin transaction")
    try:
        out["gp_group_member"] = land_records(con, ctx, SCHEMA, "gp_group_member", members,
                                              source_url=celestrak.GROUP_URL, source_updated_at=None,
                                              source_file="gp.php?FORMAT=csv")
        out["gp_group_index"] = land_records(con, ctx, SCHEMA, "gp_group_index", index,
                                             source_url=celestrak.INDEX_URL, source_updated_at=None,
                                             source_file="NORAD/elements/")
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise
    new = not_in_config([r["GROUP"] for r in index])
    if new:
        out["groups_not_in_config"] = new
    return {**out, "stage_status": "ok"}

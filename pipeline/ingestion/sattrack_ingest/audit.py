"""Custom audit tables in the permanent ops database (plan section 16.1).

Written by the Python orchestrator, so a run is recorded even when dbt crashes before
Elementary's on-run-end hooks fire. Error text is scrubbed before it is stored.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from contextlib import contextmanager

from .config import OPS_DB, connect

DDL = """
create schema if not exists audit;
create table if not exists audit.pipeline_run (
    run_id varchar primary key, started_at timestamp, finished_at timestamp, status varchar,
    trigger varchar, git_sha varchar, versions varchar, stages varchar
);
create table if not exists audit.ingestion_call (
    run_id varchar, source varchar, target_table varchar, url varchar, started_at timestamp,
    duration_s double, http_status integer, bytes bigint, rows bigint, retries integer,
    flag_skipped_fresh integer, error varchar
);
create table if not exists audit.login_state (
    service varchar primary key, consecutive_failures integer, last_failure_at timestamp,
    last_success_at timestamp, last_error varchar
);
create table if not exists audit.swap_status (
    run_id varchar, unit varchar, status varchar, as_of timestamp, detail varchar
);
create table if not exists audit.table_snapshot (
    run_id varchar, table_schema varchar, table_name varchar, row_count bigint, captured_at timestamp
);
create table if not exists audit.source_freshness (
    run_id varchar, source_table varchar, max_loaded_at timestamp, age_s double, status varchar, warn_after varchar
);
create table if not exists audit.dbt_crash_capture (
    run_id varchar, unit varchar, exit_code integer, flag_elementary_recorded integer, results varchar
);
"""

_SCRUB = [
    (re.compile(r"https?://\S+"), "<url>"),
    (re.compile(r"(?i)(password|passwd|pass|token|secret|identity)=\S+"), r"\1=<redacted>"),
    (re.compile(r"[A-Za-z]:\\[^\s'\"]+"), "<path>"),
    (re.compile(r"/(?:Users|home)/[^\s'\"]+"), "<path>"),
]


def scrub(text: str | None) -> str | None:
    if text is None:
        return None
    for pat, rep in _SCRUB:
        text = pat.sub(rep, text)
    return text[:2000]


# Yes/no columns are flag_* integers 1/0 (2026-11-09). Ops DBs created before then hold the old BOOLEAN
# columns; they are converted in place, once, when the tables are opened.
_FLAG_MIGRATIONS = [
    ("ingestion_call", "skipped_fresh", "flag_skipped_fresh"),
    ("dbt_crash_capture", "elementary_recorded", "flag_elementary_recorded"),
]


def _migrate_flags(con) -> None:
    for table, old, new in _FLAG_MIGRATIONS:
        cols = {r[0] for r in con.execute(
            "select column_name from information_schema.columns where table_schema = 'audit' and table_name = ?",
            [table]).fetchall()}
        if old in cols:
            if new not in cols:
                con.execute(f"alter table audit.{table} add column {new} integer")
            con.execute(f"update audit.{table} set {new} = cast({old} as integer)")
            con.execute(f"alter table audit.{table} drop column {old}")


@contextmanager
def ops():
    OPS_DB.parent.mkdir(parents=True, exist_ok=True)
    with connect(OPS_DB) as con:
        con.execute(DDL)
        _migrate_flags(con)
        yield con


def record_call(con, run_id: str, **kw) -> None:
    kw["error"] = scrub(kw.get("error"))
    cols = ["run_id"] + list(kw)
    con.execute(
        f"insert into audit.ingestion_call ({', '.join(cols)}) values ({', '.join('?' * len(cols))})",
        [run_id] + list(kw.values()),
    )


def login_failures(con, service: str) -> int:
    row = con.execute("select consecutive_failures from audit.login_state where service = ?", [service]).fetchone()
    return row[0] if row else 0


def record_login(con, service: str, ok: bool, error: str | None = None) -> None:
    current = login_failures(con, service)
    if ok:
        con.execute(
            "insert or replace into audit.login_state values (?, 0, (select last_failure_at from audit.login_state where service = ?), now(), null)",
            [service, service],
        )
    else:
        con.execute(
            "insert or replace into audit.login_state values (?, ?, now(), (select last_success_at from audit.login_state where service = ?), ?)",
            [service, current + 1, service, scrub(error)],
        )


def elementary_recorded(con, invocation_id: str | None) -> bool:
    """True when Elementary logged this dbt invocation (schema `elementary` in the ops DB, see dbt_project.yml).
    Only a missing table (before Elementary's first run) counts as not recorded; other errors are raised."""
    if not invocation_id:
        return False
    exists = con.execute("select count(*) from information_schema.tables "
                         "where table_schema = 'elementary' and table_name = 'dbt_invocations'").fetchone()[0]
    if not exists:
        return False
    return con.execute("select count(*) from elementary.dbt_invocations where invocation_id = ?",
                       [invocation_id]).fetchone()[0] > 0


def warning_streak(history) -> tuple[datetime, int] | None:
    """The unbroken run of warnings at the head of `history`: (first of those runs' times, number of runs).

    `history` is (status, at) pairs for one check, newest first; the newest is this run. None when the newest
    result isn't a warning. Any other status (pass, fail, error) ends the streak, so a warning that cleared and
    came back counts from its return."""
    since, runs = None, 0
    for status, at in history:
        if str(status).lower() != "warn":
            break
        since, runs = at, runs + 1
    return (since, runs) if runs else None


def _table_exists(con, schema: str, table: str) -> bool:
    return con.execute("select count(*) from information_schema.tables where table_schema = ? and table_name = ?",
                       [schema, table]).fetchone()[0] > 0


def check_warning_streaks(con, unique_ids) -> dict:
    """{dbt test unique_id: (since, runs)} for the given tests, from Elementary's result of every run
    (elementary.elementary_test_results in the ops DB, which the state script carries from run to run)."""
    ids = sorted(set(unique_ids))
    if not ids or not _table_exists(con, "elementary", "elementary_test_results"):
        return {}
    rows = con.execute("select test_unique_id, status, detected_at from elementary.elementary_test_results "
                       f"where test_unique_id in ({', '.join('?' for _ in ids)}) "
                       "order by test_unique_id, detected_at desc", ids).fetchall()
    out = {}
    for uid in ids:
        streak = warning_streak((s, at) for u, s, at in rows if u == uid)
        if streak:
            out[uid] = streak
    return out


def freshness_warning_streaks(con, sources) -> dict:
    """{source table: (since, runs)} from audit.source_freshness, one row per source per run. Run ids are
    'run_<UTC timestamp>', so they sort by time and give the run's start."""
    names = sorted(set(sources))
    if not names:
        return {}
    rows = con.execute("select source_table, status, run_id from audit.source_freshness "
                       f"where source_table in ({', '.join('?' for _ in names)}) "
                       "order by source_table, run_id desc", names).fetchall()
    out = {}
    for name in names:
        streak = warning_streak((s, datetime.strptime(r, "run_%Y-%m-%dT%H%M%SZ"))
                                for n, s, r in rows if n == name)
        if streak:
            out[name] = streak
    return out


def json_dumps(obj) -> str:
    return json.dumps(obj, default=str)

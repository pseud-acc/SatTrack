"""Ops audit tables: yes/no columns are flag_* integers 1/0; old BOOLEAN columns are migrated in place."""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sattrack_ingest import audit  # noqa: E402


def _cols(con, table):
    return dict(con.execute("select column_name, data_type from information_schema.columns "
                            "where table_schema = 'audit' and table_name = ?", [table]).fetchall())


def test_new_tables_have_integer_flags():
    con = duckdb.connect()
    con.execute(audit.DDL)
    audit._migrate_flags(con)
    assert _cols(con, "ingestion_call")["flag_skipped_fresh"] == "INTEGER"
    assert _cols(con, "dbt_crash_capture")["flag_elementary_recorded"] == "INTEGER"


def test_old_boolean_columns_migrate_once_keeping_values():
    con = duckdb.connect()
    con.execute("create schema audit")
    con.execute("create table audit.ingestion_call (run_id varchar, skipped_fresh boolean, error varchar)")
    con.execute("insert into audit.ingestion_call values ('r1', true, null), ('r2', false, null)")
    con.execute("create table audit.dbt_crash_capture (run_id varchar, elementary_recorded boolean)")
    con.execute("insert into audit.dbt_crash_capture values ('r1', false)")
    for _ in range(2):  # idempotent
        audit._migrate_flags(con)
    assert "skipped_fresh" not in _cols(con, "ingestion_call")
    assert con.execute("select run_id, flag_skipped_fresh from audit.ingestion_call order by 1").fetchall() == [("r1", 1), ("r2", 0)]
    assert con.execute("select flag_elementary_recorded from audit.dbt_crash_capture").fetchall() == [(0,)]


def test_elementary_recorded_reads_the_elementary_schema():
    con = duckdb.connect()
    assert audit.elementary_recorded(con, "abc") is False  # Elementary not run yet: no table
    con.execute("create schema elementary")
    con.execute("create table elementary.dbt_invocations (invocation_id varchar)")
    con.execute("insert into elementary.dbt_invocations values ('abc')")
    assert audit.elementary_recorded(con, "abc") is True
    assert audit.elementary_recorded(con, "xyz") is False
    assert audit.elementary_recorded(con, None) is False


# --- how long a check or source has been warning (D-037) ---------------------------------------------------------

def test_warning_streak_counts_the_unbroken_warnings_up_to_now():
    from datetime import datetime as dt
    t = [dt(2026, 11, d, 3, 17) for d in (23, 22, 21, 20, 19)]               # newest first
    assert audit.warning_streak(zip(["warn", "warn", "warn", "pass", "warn"], t)) == (t[2], 3)
    assert audit.warning_streak(zip(["WARN"], t)) == (t[0], 1)                 # case-insensitive
    assert audit.warning_streak(zip(["pass", "warn"], t)) is None             # not warning now
    assert audit.warning_streak(zip(["warn", "fail", "warn"], t)) == (t[0], 1)  # a failure ends the streak too
    assert audit.warning_streak([]) is None


def test_check_warning_streaks_read_elementary_history():
    from datetime import datetime as dt
    con = duckdb.connect()
    assert audit.check_warning_streaks(con, ["test.sattrack.x"]) == {}         # before Elementary's first run
    con.execute("create schema elementary")
    con.execute("create table elementary.elementary_test_results "
                "(test_unique_id varchar, status varchar, detected_at timestamp)")
    rows = [("test.sattrack.dup", "warn", dt(2026, 11, d, 3, 18)) for d in (21, 22, 23)]
    rows += [("test.sattrack.dup", "fail", dt(2026, 11, 18, 3, 17)), ("test.sattrack.fk", "warn", dt(2026, 11, 23, 3, 18)),
             ("test.sattrack.other", "warn", dt(2026, 11, 23, 3, 18))]
    con.executemany("insert into elementary.elementary_test_results values (?, ?, ?)", rows)
    got = audit.check_warning_streaks(con, ["test.sattrack.dup", "test.sattrack.fk", "test.sattrack.gone"])
    assert got == {"test.sattrack.dup": (dt(2026, 11, 21, 3, 18), 3), "test.sattrack.fk": (dt(2026, 11, 23, 3, 18), 1)}
    assert audit.check_warning_streaks(con, []) == {}


def test_freshness_warning_streaks_use_the_run_ids_time():
    from datetime import datetime as dt
    con = duckdb.connect()
    con.execute(audit.DDL)
    for run, st in [("run_2026-11-20T031700Z", "pass"), ("run_2026-11-21T031812Z", "warn"),
                    ("run_2026-11-22T031705Z", "warn"), ("run_2026-11-23T005138Z", "warn")]:
        con.execute("insert into audit.source_freshness values (?, 'raw_jsr.orgs', null, 0, ?, '48 hour')", [run, st])
    assert audit.freshness_warning_streaks(con, ["raw_jsr.orgs"]) == {"raw_jsr.orgs": (dt(2026, 11, 21, 3, 18, 12), 3)}
    assert audit.freshness_warning_streaks(con, ["raw_jsr.sites"]) == {}

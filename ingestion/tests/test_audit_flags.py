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

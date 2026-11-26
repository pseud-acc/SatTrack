"""run_pipeline.drop_orphans (phase 0 finding, D-047): tables no current model, source or seed owns are dropped before
the swap; seed tables (raw_sattrack, D-047) are declared like sources and survive."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import duckdb

# run_pipeline imports the HTTP extractors, which need `requests`; the tests' environment (CI) doesn't install it and
# drop_orphans never calls them, so a stand-in module is enough.
sys.modules.setdefault("requests", types.ModuleType("requests"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import run_pipeline  # noqa: E402


def manifest(tmp_path: Path, unit: str) -> None:
    nodes = {
        "model.sattrack.stg__sattrack__manual_satellite_grouping": {
            "resource_type": "model", "package_name": "sattrack", "schema": "staging",
            "name": "stg__sattrack__manual_satellite_grouping"},
        "seed.sattrack.manual_satellite_grouping": {
            "resource_type": "seed", "package_name": "sattrack", "schema": "raw_sattrack",
            "name": "manual_satellite_grouping"},
    }
    sources = {"source.sattrack.celestrak.group_config": {
        "package_name": "sattrack", "schema": "raw_celestrak", "name": "group_config"}}
    path = tmp_path / "target" / unit / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"nodes": nodes, "sources": sources}), encoding="utf-8")


def test_seed_tables_survive_and_retired_raw_tables_go(tmp_path, monkeypatch):
    db = tmp_path / "build.duckdb"
    with duckdb.connect(str(db)) as con:
        for ddl in ("create schema raw_sattrack", "create table raw_sattrack.manual_satellite_grouping (x int)",
                    "create schema raw_celestrak", "create table raw_celestrak.group_config (x int)",
                    "create table raw_celestrak.retired_table (x int)",
                    "create schema staging", "create table staging.stg__sattrack__manual_satellite_grouping (x int)",
                    "create table staging.stg__retired_model (x int)"):
            con.execute(ddl)
    for unit in run_pipeline.UNITS:
        manifest(tmp_path, unit)
    monkeypatch.setattr(run_pipeline, "TRANSFORM", tmp_path)
    monkeypatch.setattr(run_pipeline, "BUILD_DB", db)
    dropped = run_pipeline.drop_orphans()
    assert sorted(dropped) == ["raw_celestrak.retired_table", "staging.stg__retired_model"]
    with duckdb.connect(str(db)) as con:
        kept = {f"{s}.{t}" for s, t in con.execute("select schema_name, table_name from duckdb_tables()").fetchall()}
    assert "raw_sattrack.manual_satellite_grouping" in kept

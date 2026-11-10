"""Per-run summary log: date-partitioned path, command and stage results, problems named, no dbt output."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sattrack_ingest import runlog  # noqa: E402

STARTED = datetime(2026, 11, 10, 20, 39, 14, tzinfo=timezone.utc)
FINISHED = datetime(2026, 11, 10, 20, 41, 30, tzinfo=timezone.utc)


def _render(**kw):
    args = dict(run_id="run_2026-11-10T203914Z", command="run_pipeline.py --quiet", trigger="manual", git_sha=None,
                versions={"python": "3.12.3", "dbt": "2.0.8"}, started=STARTED, finished=FINISHED, overall="warn",
                units={"tracking": "ok", "enrichment": "ok"},
                stages=[
                    {"stage": "ingest:spacetrack", "status": "ok", "duration_s": 4.8, "rows": {"gp": 32665}},
                    {"stage": "ingest:gcat", "status": "ok", "duration_s": 0.1, "rows": {"satcat": "skipped_fresh"}},
                    {"stage": "source_freshness", "status": "warn", "sources": 15,
                     "not_pass": ["spacetrack.boxscore warn: 20.8 h old (warn after 12 hour)"]},
                    {"stage": "dbt:enrichment", "status": "ok", "duration_s": 92.1, "exit_code": 0,
                     "statuses": {"success": 72, "pass": 175, "warn": 1},
                     "issues": [{"node": "fk__dim__org__org_parent_code", "status": "warn", "failures": 2}]},
                ],
                reports={"health": 0, "summary": 0, "app_csv": 1},
                row_changes=[("marts.fct__satellite_master", 32665, 32600), ("marts.dim__country", 280, 280)])
    args.update(kw)
    return runlog.render(**args)


def test_path_is_date_partitioned_and_named_by_run():
    p = runlog.log_path(Path("/data"), "run_2026-11-10T203914Z", STARTED)
    assert p.as_posix() == "/data/logs/2026/11/10/run_2026-11-10T203914Z.log"


def test_summary_names_command_results_and_problems():
    text = _render()
    assert "command   run_pipeline.py --quiet" in text
    assert "result    WARN" in text and "(2m 16s)" in text
    assert "rows gp=32,665" in text and "skipped as fresh: satcat" in text
    assert "spacetrack.boxscore warn: 20.8 h old" in text
    assert "pass=175" in text and "warn: fk__dim__org__org_parent_code (2 rows)" in text
    assert "app_csv=exit 1" in text
    st = _render(stages=[{"stage": "ingest:spacetrack", "status": "ok", "rows": {"skipped_fresh": ["gp", "boxscore"]}}])
    assert "skipped as fresh: gp, boxscore" in st
    assert "+65" in text and "no change" in text


def test_crash_and_error_are_shown():
    text = _render(overall="error", crash="RuntimeError: boom",
                   stages=[{"stage": "ingest:spacetrack", "status": "error", "duration_s": 0.2, "error": "LoginError"}])
    assert "crashed   RuntimeError: boom" in text and "error: LoginError" in text


def test_write_creates_folders(tmp_path):
    p = runlog.write(runlog.log_path(tmp_path, "run_x", STARTED), "x\n")
    assert p.read_text(encoding="utf-8") == "x\n"

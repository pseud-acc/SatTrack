"""Unit tests: the public run report and alert (.github/scripts/pipeline_report.py), run as pipeline.yml runs it.

Scope: each alert rule (exit code, a unit not published, failed S3 commit, no summary, no export, stale positions
or details); warnings (a warn check, a stale source) don't fail the job but set status=warning with a summary for
the issue, each with how long it has been warning (D-037); the gate skip doesn't alert; and the public output never
repeats the private summary's row counts, mart table sizes or other data. Summaries are shaped like real run logs.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "pipeline_report.py"

HELD = """SatTrack run run_2026-11-18T031752Z
command   run_pipeline.py
trigger   eventbridge    git 15fd711e14d9cb8a9f406ad8e00d94bf43a66831    python 3.12.3  duckdb 2.0.0  dbt 2.0.8
started   2026-11-18 03:17:52 UTC
finished  2026-11-18 03:18:28 UTC  (36s)
result    WARN    tracking=ok  enrichment=held

stages
  ingest:spacetrack   ok           8s  rows gp=32,730, boxscore=122
  ingest:gcat         ok           4s  rows satcat=69,999, launchlog=32,213
  dbt:tracking        ok           4s  pass=18, success=34; exit 0
  dbt:enrichment      error       16s  fail=1, pass=139, skipped=40, success=66, warn=2; exit 1
                                         skipped: fct__satellite_master
                                         skipped: mh__fct__satellite_master__pk_unique
                                         warn: fk__dim__org__org_parent_code (2 rows)
                                         fail: mh__int__jsr__launch_events__pk_unique (2 rows)
  publish:tracking    ok               published this run
  publish:enrichment  held             kept last good build
  swap                ok               renamed build DB over live DB

reports   health=ok  summary=ok  app_csv=ok

mart rows (change since previous run)
  marts.fct__satellite_master                32,672  no change
  marts_tracking.fct__gp_elements            32,730  +58
"""
CLEAN = (HELD.replace("result    WARN    tracking=ok  enrichment=held", "result    OK    tracking=ok  enrichment=ok")
         .replace("dbt:enrichment      error", "dbt:enrichment      ok   ")
         .replace("                                         skipped: fct__satellite_master\n", "")
         .replace("                                         skipped: mh__fct__satellite_master__pk_unique\n", "")
         .replace("                                         fail: mh__int__jsr__launch_events__pk_unique (2 rows)\n", "")
         .replace("publish:enrichment  held             kept last good build", "publish:enrichment  ok               published this run"))
# No check or source warning at all.
SPOTLESS = CLEAN.replace("                                         warn: fk__dim__org__org_parent_code (2 rows)\n", "")
# The 23 Nov run: every unit published, but a source was stale (result WARN) and two checks warned, one of them
# for 3 runs in a row.
STALE_SOURCE = (CLEAN.replace("result    OK    tracking=ok  enrichment=ok", "result    WARN    tracking=ok  enrichment=ok")
                .replace("  dbt:tracking        ok ",
                         "  source_freshness    warn             12 sources checked\n"
                         "                                         not pass: raw_jsr.orgs warn: 75.3 h old (warn after 48 hour)"
                         " since 2026-11-21 03:18 UTC (3 runs)\n"
                         "  dbt:tracking        ok ")
                .replace("warn: fk__dim__org__org_parent_code (2 rows)",
                         "warn: fk__dim__org__org_parent_code (2 rows) since 2026-11-15 03:17 UTC (1 run)\n"
                         "                                         warn: mh__stg__jsr__launchlog__pk_unique (2 rows)"
                         " since 2026-11-21 03:18 UTC (3 runs)"))


def outputs(tmp_path):
    """GITHUB_OUTPUT as {name: value} (the report writes name<<SATTRACK_EOF blocks)."""
    text = (tmp_path / "github_output.txt").read_text(encoding="utf-8")
    return {m[0]: m[1] for m in re.findall(r"(\w+)<<SATTRACK_EOF\n(.*?)\nSATTRACK_EOF\n", text, re.S)}


def run(tmp_path, summary=CLEAN, positions_age_h=19.0, details_age_d=1.9, manifest=True, **env):
    data = tmp_path / "data"
    if summary is not None:
        log = data / "logs" / "2026" / "11" / "18" / "run_2026-11-18T031752Z.log"
        log.parent.mkdir(parents=True)
        log.write_text(summary, encoding="utf-8")
    if manifest:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        (data / "app").mkdir(parents=True, exist_ok=True)
        (data / "app" / "manifest.json").write_text(json.dumps({
            "run_id": "run_2026-11-18T031752Z",
            "positions_as_of": (now - timedelta(hours=positions_age_h)).isoformat(),
            "details_run_id": "run_2026-11-16T234648Z",
            "details_built_at": (now - timedelta(days=details_age_d)).isoformat(),
            "gcat_updated_at": "2026-11-15T10:18:40",
        }), encoding="utf-8")
    step_summary = tmp_path / "step_summary.md"
    full_env = {**os.environ, "SATTRACK_DATA_DIR": str(data), "GATE": "true", "PIPELINE_EXIT": "0",
                "PUSH_OUTCOME": "success", "GITHUB_STEP_SUMMARY": str(step_summary),
                "GITHUB_OUTPUT": str(tmp_path / "github_output.txt"), **env}
    p = subprocess.run([sys.executable, str(SCRIPT)], env=full_env, capture_output=True, text=True)
    page = step_summary.read_text(encoding="utf-8") if step_summary.exists() else ""
    return p.returncode, p.stdout, page


def test_spotless_run_is_ok(tmp_path):
    code, out, page = run(tmp_path, summary=SPOTLESS)
    assert code == 0 and "::error" not in out and "::warning" not in out
    assert "Positions (Space-Track GP) as of:" in out and "(19.0 h ago)" in out
    assert "Details (GCAT) built:" in out and "GCAT catalogue updated 2026-11-15" in out
    assert "**OK**" in page
    assert outputs(tmp_path)["status"] == "ok"


def test_warn_check_is_a_warning_not_a_failure(tmp_path):
    code, out, page = run(tmp_path)
    assert code == 0 and "::error" not in out
    assert "Result: OK tracking=ok enrichment=ok" in out
    assert "warn: fk__dim__org__org_parent_code (2 rows)" in out
    assert "::warning title=SatTrack pipeline warnings::1 warning(s); data published" in out
    assert "**Warnings:** 1, data published" in page
    o = outputs(tmp_path)
    assert o["status"] == "warning" and "warn: fk__dim__org__org_parent_code (2 rows)" in o["body"]


def test_stale_source_with_every_unit_published_is_a_warning_with_how_long(tmp_path):
    """The 23 Nov run (45091163953): result WARN from source freshness, data published. Not a failure."""
    code, out, _ = run(tmp_path, summary=STALE_SOURCE)
    assert code == 0 and "::error" not in out
    assert "::warning title=SatTrack pipeline warnings::3 warning(s); data published" in out
    assert re.search(r"freshness warn: raw_jsr\.orgs 75\.3 h old \(warn after 48 hour\), warning for "
                     r"\d+\.\d days \(3 runs, since 2026-11-21 03:18 UTC\)", out)
    assert re.search(r"warn: mh__stg__jsr__launchlog__pk_unique \(2 rows\), warning for \d+\.\d days "
                     r"\(3 runs, since 2026-11-21 03:18 UTC\)", out)
    assert "(1 run, since 2026-11-15 03:17 UTC)" in out           # singular
    o = outputs(tmp_path)
    assert o["status"] == "warning"
    assert o["body"].startswith("**Warnings:** 3, data published")
    assert "raw_jsr.orgs" in o["body"] and "Details are in the private log in S3." in o["body"]


def test_held_unit_alerts_and_names_the_failing_check(tmp_path):
    """The 18 Nov run: exit 0, data promoted, but enrichment held."""
    code, out, page = run(tmp_path, summary=HELD)
    assert code == 1
    assert "::error title=SatTrack pipeline needs attention::pipeline result WARN" in out
    assert "fail: mh__int__jsr__launch_events__pk_unique (2 rows)" in out
    assert "dbt:enrichment=error" in out and "publish:enrichment=held" in out
    assert "(2 downstream models/tests skipped)" in out
    assert "**Problems:** pipeline result WARN" in page
    assert outputs(tmp_path)["status"] == "problem"


@pytest.mark.parametrize("kwargs, problem", [
    ({"PIPELINE_EXIT": "1"}, "pipeline exit code 1"),
    ({"PIPELINE_EXIT": ""}, "pipeline exit code none"),
    ({"PUSH_OUTCOME": "failure"}, "committing state to S3: failure"),
    ({"summary": None}, "pipeline result missing"),
    ({"manifest": False}, "no app export"),
    ({"positions_age_h": 31.0}, "positions older than 30 h"),
    ({"details_age_d": 15.0}, "details older than 14 days"),
], ids=["exit-1", "no-exit-code", "push-failed", "no-summary", "no-export", "stale-positions", "stale-details"])
def test_each_problem_alerts(tmp_path, kwargs, problem):
    code, out, _ = run(tmp_path, **kwargs)
    assert code == 1
    assert problem in out.splitlines()[-1]


def test_gate_skip_does_not_alert(tmp_path):
    code, out, page = run(tmp_path, summary=None, manifest=False, GATE="false")
    assert code == 0 and "skipped by the 12-hour gate" in out and "**Skipped.**" in page
    assert outputs(tmp_path)["status"] == "skipped"


def test_public_output_holds_no_data(tmp_path):
    """Only result, stage statuses, check names and dates go public; never the summary's counts or tables."""
    code, out, page = run(tmp_path, summary=HELD)
    for text in (out, page, outputs(tmp_path)["body"]):
        for private in ("32,730", "69,999", "boxscore", "launchlog=", "marts_tracking.fct__gp_elements",
                        "32,672", "15fd711e", "renamed build DB", "kept last good build"):
            assert private not in text, private

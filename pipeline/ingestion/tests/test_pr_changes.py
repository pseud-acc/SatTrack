"""Tests: .github/scripts/pr_changes.py, which decides the checks a pull request needs (pr.yml's `changes` job)."""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "pr_changes.py"
spec = importlib.util.spec_from_file_location("pr_changes", SCRIPT)
pr_changes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr_changes)

NONE = dict(app_build=False, app_tests=False, app_e2e=False, pipeline=False)
APP = dict(app_build=True, app_tests=True, app_e2e=True, pipeline=False)
ALL = dict(app_build=True, app_tests=True, app_e2e=True, pipeline=True)


def need(*paths):
    return pr_changes.decide(paths)[0]


@pytest.mark.parametrize("paths", [
    ["docs/DECISIONS.md", "docs/decisions/D-044-design-direction.md", "docs/ROADMAP.md"],   # PR #74's shape
    ["README.md", "CHANGELOG.md", "CLAUDE.md", "app/README.md", "LICENSE"],
])
def test_docs_only_runs_nothing(paths):
    assert need(*paths) == NONE


@pytest.mark.parametrize("path", ["app/core/viewer.py", "static/viewer/viewer.js", "assets/03_tokens.css",
                                  "run_app.py", "pyproject.toml", "uv.lock", "Procfile", "bin/post_compile",
                                  "vendor/cesium.lock"])
def test_app_files_run_the_app_checks(path):
    assert need(path) == APP


def test_app_contracts_also_run_the_pipeline():
    assert need("app/contracts/objects.schema.json") == ALL


@pytest.mark.parametrize("path", ["pipeline/run_pipeline.py", "pipeline/transform/models/marts/x.sql",
                                  "pipeline/docs/column_definitions/celestrak__groups.md",
                                  "pipeline/transform/docs/columns/sattrack__derived.md", "infra/state/sattrack_state.py",
                                  ".github/scripts/pipeline_report.py", ".github/workflows/pipeline-checks.yml"])
def test_pipeline_files_run_only_the_pipeline(path):
    assert need(path) == dict(NONE, pipeline=True)


def test_test_only_changes_run_their_own_suite():
    assert need("tests/e2e/test_viewer.py") == dict(NONE, app_e2e=True)
    assert need("tests/app/test_viewer.py") == dict(NONE, app_tests=True, app_e2e=True)   # e2e imports tests/app/_support
    assert need("tests/app_data/objects.json.br") == APP
    assert need("tests/contracts/filter_spec_cases.json") == dict(ALL, app_build=False)   # no build needed


def test_each_check_workflow_runs_itself():
    assert need(".github/workflows/app-build.yml") == dict(NONE, app_build=True)
    assert need(".github/scripts/heroku_build_check.sh") == dict(NONE, app_build=True)
    assert need(".github/workflows/app-e2e.yml") == dict(NONE, app_e2e=True)


@pytest.mark.parametrize("path", [".github/workflows/pr.yml", ".github/scripts/pr_changes.py",
                                  ".github/workflows/something-new.yml", "tests/new_suite/test_x.py"])
def test_the_gate_and_unknown_paths_run_everything(path):
    assert need(path) == ALL


def test_main_writes_outputs_and_falls_back_to_everything(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert pr_changes.main(["--all"]) == 0
    assert out.read_text().split() == ["app_build=true", "app_tests=true", "app_e2e=true", "pipeline=true"]
    out.unlink()
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(""))   # an empty file list is suspicious: run everything
    pr_changes.main([])
    assert "pipeline=true" in out.read_text()
    out.unlink()
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("docs/ROADMAP.md\n"))
    pr_changes.main([])
    assert out.read_text().split() == ["app_build=false", "app_tests=false", "app_e2e=false", "pipeline=false"]

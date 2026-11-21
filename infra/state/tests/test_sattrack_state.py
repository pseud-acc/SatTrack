"""Tests: infra/state/sattrack_state.py, the script that decides what goes live (pull before a run, push after it).

Scope: the 12-hour gate and pull verification; which builds are promoted (ok / warn / error / crash / failed
integrity check); the manifest compare-and-swap that stops a concurrent run overwriting a newer commit; the dry
run; private logs; raw history; publishing the app data (both CSVs from one run, pointer written last, a bad
export leaves the app data untouched); the one-time seed.

S3 is a fake client (below) that keeps versions, ETags and conditional writes (If-Match / If-None-Match) the way
S3 does, checks the SHA-256 sent with each upload, and records the order of writes. The live and ops databases
are real DuckDB files. Expected outcomes are written out in each test.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import io
import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pytest

# ---- botocore: the script only catches ClientError and reads its error code. Use the real class when installed
# (CI's test environment doesn't have boto3), else a stand-in with the same .response shape.
try:
    from botocore.exceptions import ClientError
except ImportError:
    class ClientError(Exception):
        def __init__(self, error_response, operation_name):
            super().__init__(f"{operation_name}: {error_response['Error']['Code']}")
            self.response = error_response
    _exc = types.ModuleType("botocore.exceptions")
    _exc.ClientError = ClientError
    sys.modules.setdefault("botocore", types.ModuleType("botocore"))
    sys.modules["botocore.exceptions"] = _exc

SCRIPT = Path(__file__).resolve().parents[1] / "sattrack_state.py"
spec = importlib.util.spec_from_file_location("sattrack_state", SCRIPT)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)

BUCKET = "test-bucket"
NOW = datetime(2026, 11, 19, 3, 17, 52, tzinfo=timezone.utc)


def _err(code, op):
    return ClientError({"Error": {"Code": code}}, op)


class FakeS3:
    """In-memory S3 with versioning: get_object, put_object (IfMatch / IfNoneMatch / ChecksumSHA256),
    download_file (by VersionId). `writes` lists every successful put in order."""

    def __init__(self):
        self.objects = {}      # key -> list of (version_id, bytes, etag); last is current
        self.writes = []
        self._n = 0

    def _current(self, key):
        return self.objects[key][-1] if self.objects.get(key) else None

    def get_object(self, Bucket, Key, VersionId=None):
        assert Bucket == BUCKET
        cur = self._current(Key)
        if cur is None:
            raise _err("NoSuchKey", "GetObject")
        return {"Body": io.BytesIO(cur[1]), "ETag": cur[2], "VersionId": cur[0]}

    def put_object(self, Bucket, Key, Body, IfMatch=None, IfNoneMatch=None, ChecksumSHA256=None, ContentType=None):
        assert Bucket == BUCKET
        data = Body if isinstance(Body, bytes) else Body.read()
        cur = self._current(Key)
        if IfNoneMatch == "*" and cur is not None:
            raise _err("PreconditionFailed", "PutObject")
        if IfMatch is not None and (cur is None or cur[2] != IfMatch):
            raise _err("PreconditionFailed", "PutObject")
        if ChecksumSHA256 is not None:
            assert base64.b64decode(ChecksumSHA256) == hashlib.sha256(data).digest(), f"bad checksum for {Key}"
        self._n += 1
        version, etag = f"v{self._n}", f'"{hashlib.md5(data).hexdigest()}"'
        self.objects.setdefault(Key, []).append((version, data, etag))
        self.writes.append(Key)
        return {"VersionId": version, "ETag": etag}

    def download_file(self, bucket, key, dest, ExtraArgs=None):
        assert bucket == BUCKET
        version = (ExtraArgs or {}).get("VersionId")
        data = next(d for v, d, _ in self.objects[key] if v == version)
        Path(dest).write_bytes(data)

    # helpers for tests
    def body(self, key):
        return self._current(key)[1]

    def json(self, key):
        return json.loads(self.body(key))

    def versions(self, key):
        return [v for v, _, _ in self.objects.get(key, [])]


# ---- databases -------------------------------------------------------------------------------------------------

def make_ops(path: Path, runs: list[tuple[str, str, datetime]]):
    """Ops DB with audit.pipeline_run rows (run_id, status, started_at)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as con:
        con.execute("create schema audit")
        con.execute("create table audit.pipeline_run (run_id varchar primary key, started_at timestamp, "
                    "finished_at timestamp, status varchar, trigger varchar, git_sha varchar, versions varchar, "
                    "stages varchar)")
        for run_id, status, started in runs:
            con.execute("insert into audit.pipeline_run (run_id, started_at, status) values (?, ?, ?)",
                        [run_id, started.replace(tzinfo=None), status])


def make_live(path: Path, master_rows=3, gp_rows=4, tag="build"):
    """Live DB with the two marts the integrity check requires; `tag` makes each build's bytes distinct."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as con:
        con.execute("create schema marts; create schema marts_tracking")
        con.execute("create table marts.fct__satellite_master (satcat_id integer, tag varchar)")
        con.execute("create table marts_tracking.fct__gp_elements (satcat_id integer, tag varchar)")
        for i in range(master_rows):
            con.execute("insert into marts.fct__satellite_master values (?, ?)", [i, tag])
        for i in range(gp_rows):
            con.execute("insert into marts_tracking.fct__gp_elements values (?, ?)", [i, tag])


# ---- fixtures --------------------------------------------------------------------------------------------------

PRIOR = "run_2026-11-18T231949Z"
PRIOR_AT = datetime(2026, 11, 18, 23, 19, 49)


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A committed state in fake S3 (as after the 18 Nov 23:19 run), a data dir, and the script's clock."""
    s3 = FakeS3()
    monkeypatch.setattr(state, "s3", lambda: s3)
    monkeypatch.setattr(state, "utcnow", lambda: NOW)
    monkeypatch.setenv("SATTRACK_S3_BUCKET", BUCKET)
    data = tmp_path / "data"
    monkeypatch.setenv("SATTRACK_DATA_DIR", str(data))
    out = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    for var in ("GITHUB_RUN_ID", "GITHUB_SHA", "SATTRACK_TRIGGER"):
        monkeypatch.delenv(var, raising=False)

    # committed state: live + ops DBs and a manifest naming their versions
    seed = tmp_path / "seed"
    make_live(seed / "sattrack.duckdb", tag="committed")
    make_ops(seed / "sattrack_ops.duckdb", [(PRIOR, "warn", PRIOR_AT)])
    live = state.put_file(s3, state.LIVE_KEY, seed / "sattrack.duckdb")
    live["run_id"] = PRIOR
    manifest = {"schema": 1, "live": live, "ops": state.put_file(s3, state.OPS_KEY, seed / "sattrack_ops.duckdb"),
                "last_ok_at": (NOW - timedelta(hours=27)).isoformat(),
                "last_run": {"run_id": PRIOR, "status": "warn", "promoted_live": True}}
    s3.put_object(Bucket=BUCKET, Key=state.MANIFEST_KEY, Body=json.dumps(manifest).encode())
    s3.writes.clear()
    return types.SimpleNamespace(s3=s3, data=data, out=out, manifest=manifest)


def outputs(env):
    return dict(l.split("=", 1) for l in env.out.read_text().split()) if env.out.exists() else {}


def pull(force=False, min_hours=12.0):
    return state.cmd_pull(argparse.Namespace(force=force, min_hours=min_hours))


def push(exit_code=0, log_file=None, dry_run=False):
    return state.cmd_push(argparse.Namespace(pipeline_exit=exit_code, log_file=log_file, dry_run=dry_run))


def run_pipeline(env, status="ok", run_id="run_2026-11-19T031752Z", live_ok=True, export=True, summary=True):
    """What run_pipeline.py leaves in the data dir: a new pipeline_run row, a rebuilt live DB, the run summary,
    raw history, report pages and the app export (CSVs + manifest with their SHA-256)."""
    wh = env.data / "warehouse"
    new_row = [] if run_id == PRIOR else [(run_id, status, NOW.replace(tzinfo=None))]   # PRIOR: crashed, no row
    make_ops(wh / "sattrack_ops.duckdb", [(PRIOR, "warn", PRIOR_AT)] + new_row)
    make_live(wh / "sattrack.duckdb", master_rows=3 if live_ok else 0, tag=run_id)
    if summary:
        log = env.data / "logs" / "2026" / "11" / "19" / f"{run_id}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"SatTrack run {run_id}\nresult    {status.upper()}\n", encoding="utf-8")
    raw = env.data / "raw_history" / "raw_spacetrack" / "gp" / f"{run_id}.parquet"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(b"PAR1 fake parquet " + run_id.encode())
    for page in ("health/health.html", "health/health.json", "reports/data_summary.html"):
        (env.data / page).parent.mkdir(parents=True, exist_ok=True)
        (env.data / page).write_text(f"{page} {run_id}", encoding="utf-8")
    if export:
        app = env.data / "app"
        app.mkdir(parents=True, exist_ok=True)
        (app / "satcat_tle.csv").write_text("SatCatId,ObjectName\n25544,ISS (ZARYA)\n", encoding="utf-8")
        (app / "last_data_update.csv").write_text("Source,Last Download,Last Update\n", encoding="utf-8")
        files = [{"file": n, "rows": r, "sha256": state.sha256_file(app / n)}
                 for n, r in (("satcat_tle.csv", 1), ("last_data_update.csv", 0))]
        (app / "manifest.json").write_text(json.dumps({"run_id": run_id, "generated_at": NOW.isoformat(),
                                                       "files": files}), encoding="utf-8")
    return run_id


# ---- pull ------------------------------------------------------------------------------------------------------

def test_pull_without_committed_state_refuses_to_run(env):
    env.s3.objects.pop(state.MANIFEST_KEY)
    assert pull() == 1
    assert outputs(env) == {"run": "false"}
    assert not (env.data / "warehouse").exists()


@pytest.mark.parametrize("hours_ago, force, runs", [
    (3, False, False),      # 18 Nov 23:19 manual run -> 03:17 EventBridge run skipped (as on 17 Nov)
    (11.9, False, False),
    (12.1, False, True),
    (3, True, True),        # force overrides the gate
], ids=["3h", "11.9h", "12.1h", "3h-forced"])
def test_pull_gate(env, hours_ago, force, runs):
    manifest = dict(env.manifest, last_ok_at=(NOW - timedelta(hours=hours_ago)).isoformat())
    env.s3.put_object(Bucket=BUCKET, Key=state.MANIFEST_KEY, Body=json.dumps(manifest).encode())
    assert pull(force=force) == 0
    assert outputs(env) == {"run": "true" if runs else "false"}
    assert (env.data / "warehouse" / "sattrack.duckdb").exists() == runs


def test_pull_gate_counts_from_the_last_ok_run_only(env):
    """last_ok_at moves only on status ok: after 'warn' runs (enrichment held) every run goes ahead."""
    manifest = dict(env.manifest, last_ok_at=None)
    env.s3.put_object(Bucket=BUCKET, Key=state.MANIFEST_KEY, Body=json.dumps(manifest).encode())
    assert pull() == 0 and outputs(env) == {"run": "true"}


def test_pull_downloads_committed_versions_and_records_the_pull(env):
    assert pull() == 0
    wh = env.data / "warehouse"
    assert state.sha256_file(wh / "sattrack.duckdb") == env.manifest["live"]["sha256"]
    assert state.sha256_file(wh / "sattrack_ops.duckdb") == env.manifest["ops"]["sha256"]
    marker = json.loads((env.data / ".state" / "pull.json").read_text())
    assert marker["etag"] == env.s3.get_object(Bucket=BUCKET, Key=state.MANIFEST_KEY)["ETag"]
    assert marker["prior_run_id"] == PRIOR and marker["manifest"] == env.manifest


def test_pull_refuses_a_download_that_fails_its_checksum(env):
    manifest = dict(env.manifest, live=dict(env.manifest["live"], sha256="0" * 64))
    env.s3.put_object(Bucket=BUCKET, Key=state.MANIFEST_KEY, Body=json.dumps(manifest).encode())
    with pytest.raises(SystemExit, match="checksum mismatch for warehouse/sattrack.duckdb"):
        pull()
    assert not (env.data / "warehouse" / "sattrack.duckdb").exists()   # the unverified file is deleted


# ---- push: what gets promoted ----------------------------------------------------------------------------------

def test_push_ok_run_promotes_everything_and_moves_the_gate(env):
    pull()
    run_id = run_pipeline(env, status="ok")
    assert push() == 0
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"]["run_id"] == run_id and m["live"]["sha256"] == state.sha256_file(env.data / "warehouse" / "sattrack.duckdb")
    assert m["ops"]["version_id"] == env.s3.versions(state.OPS_KEY)[-1]
    assert m["last_ok_at"] == NOW.isoformat()
    assert m["last_run"] == {"run_id": run_id, "status": "ok", "promoted_live": True, "at": NOW.isoformat(),
                             "github_run_id": None, "git_sha": None, "trigger": None}
    assert env.s3.json(state.APP_POINTER_KEY)["run_id"] == run_id
    assert env.s3.body("reports/health/health.html").decode().endswith(run_id)


def test_push_warn_run_is_promoted_but_does_not_move_the_gate(env):
    """18 Nov: enrichment held -> status warn. The build (fresh tracking) goes live; last_ok_at stays."""
    pull()
    run_id = run_pipeline(env, status="warn")
    assert push() == 0
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"]["run_id"] == run_id and m["last_run"]["promoted_live"] is True
    assert m["last_ok_at"] == env.manifest["last_ok_at"]
    assert env.s3.json(state.APP_POINTER_KEY)["run_id"] == run_id


@pytest.mark.parametrize("status, exit_code", [("error", 1), ("error", 0)])
def test_push_failed_run_keeps_the_last_good_build(env, status, exit_code):
    pull()
    run_id = run_pipeline(env, status=status)
    assert push(exit_code) == (1 if exit_code else 0)
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"] == env.manifest["live"]                       # last good build stays live
    assert m["ops"]["version_id"] == env.s3.versions(state.OPS_KEY)[-1]   # login backoff etc. remembered
    assert m["last_run"]["run_id"] == run_id and m["last_run"]["status"] == status
    assert m["last_run"]["promoted_live"] is False
    assert state.APP_POINTER_KEY not in env.s3.objects and "reports/health/health.html" not in env.s3.objects


def test_push_after_a_crash_records_it_and_promotes_nothing(env):
    """The pipeline never wrote a new pipeline_run row (crashed before finishing)."""
    pull()
    run_pipeline(env, status="ok", run_id=PRIOR, summary=False)   # same newest row as before the run
    console = env.data / "console.log"
    console.write_text("Traceback ...", encoding="utf-8")
    assert push(exit_code=1, log_file=str(console)) == 1
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"] == env.manifest["live"]
    assert m["last_run"]["status"] == "crashed" and m["last_run"]["run_id"] is None
    assert any(k.startswith("logs/2026/11/19/") and k.endswith("_console.log") for k in env.s3.objects)


def test_push_holds_a_build_that_fails_the_integrity_check(env):
    pull()
    run_pipeline(env, status="ok", live_ok=False)        # fct__satellite_master empty
    assert push() == 0
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"] == env.manifest["live"] and m["last_run"]["promoted_live"] is False
    assert m["last_ok_at"] == env.manifest["last_ok_at"]
    assert state.APP_POINTER_KEY not in env.s3.objects


def test_push_with_an_unreadable_ops_db_commits_nothing(env):
    pull()
    run_pipeline(env)
    (env.data / "warehouse" / "sattrack_ops.duckdb").write_bytes(b"not a database")
    before = env.s3.body(state.MANIFEST_KEY)
    assert push() == 1
    assert env.s3.body(state.MANIFEST_KEY) == before
    assert state.OPS_KEY not in [w for w in env.s3.writes]


# ---- push: commit point, ordering, dry run, logs, raw history ----------------------------------------------------

def test_push_refuses_to_overwrite_a_newer_commit(env):
    """Another run committed after this one pulled: the If-Match on the pulled ETag fails, nothing changes."""
    pull()
    run_pipeline(env)
    newer = dict(env.manifest, last_run={"run_id": "run_other", "status": "ok", "promoted_live": True})
    env.s3.put_object(Bucket=BUCKET, Key=state.MANIFEST_KEY, Body=json.dumps(newer).encode())
    assert push() == 1
    assert env.s3.json(state.MANIFEST_KEY) == newer
    assert state.APP_POINTER_KEY not in env.s3.objects            # app data only after a successful commit


def test_push_order_manifest_then_app_csvs_then_pointer_last(env):
    pull()
    run_pipeline(env)
    push()
    w = env.s3.writes
    assert w.index(state.MANIFEST_KEY) < w.index("app/satcat_tle.csv")
    assert max(w.index("app/satcat_tle.csv"), w.index("app/last_data_update.csv"),
               w.index("app/manifest.json")) < w.index(state.APP_POINTER_KEY)
    assert w[-1] == state.APP_POINTER_KEY


def test_app_pointer_names_the_exact_versions_and_checksums(env):
    pull()
    run_id = run_pipeline(env)
    push()
    p = env.s3.json(state.APP_POINTER_KEY)
    assert p["run_id"] == run_id and p["export_run_id"] == run_id and p["published_at"] == NOW.isoformat()
    for name in state.APP_CSVS:
        entry = p["files"][name]
        assert entry["version_id"] == env.s3.versions(f"app/{name}")[-1]
        assert entry["sha256"] == hashlib.sha256(env.s3.body(f"app/{name}")).hexdigest()
    assert p["files"]["satcat_tle.csv"]["rows"] == 1


def test_a_bad_export_leaves_the_app_data_unchanged(env):
    """A CSV that doesn't match the export's own checksum: DB and manifest are committed, app data is not."""
    pull()
    run_pipeline(env)
    (env.data / "app" / "satcat_tle.csv").write_text("SatCatId,ObjectName\n", encoding="utf-8")
    assert push() == 0
    assert env.s3.json(state.MANIFEST_KEY)["last_run"]["promoted_live"] is True
    assert not any(k.startswith("app/") for k in env.s3.objects)


def test_dry_run_uploads_only_the_log(env):
    pull()
    run_id = run_pipeline(env)
    before = env.s3.body(state.MANIFEST_KEY)
    assert push(dry_run=True) == 0
    assert env.s3.writes == [f"logs/2026/11/19/{run_id}.log"]
    assert env.s3.body(state.MANIFEST_KEY) == before


def test_raw_history_is_uploaded_write_once_even_for_a_held_build(env):
    pull()
    run_id = run_pipeline(env, status="error")
    push(exit_code=1)
    assert f"raw_history/raw_spacetrack/gp/{run_id}.parquet" in env.s3.objects


def test_run_metadata_comes_from_the_workflow(env, monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "44419709887")
    monkeypatch.setenv("GITHUB_SHA", "a730304")
    monkeypatch.setenv("SATTRACK_TRIGGER", "manual")
    pull()
    run_pipeline(env)
    push()
    last = env.s3.json(state.MANIFEST_KEY)["last_run"]
    assert (last["github_run_id"], last["git_sha"], last["trigger"]) == ("44419709887", "a730304", "manual")


# ---- seed ------------------------------------------------------------------------------------------------------

def test_seed_refuses_when_state_exists(env):
    with pytest.raises(SystemExit, match="state already exists"):
        state.cmd_seed(argparse.Namespace())


def test_seed_creates_the_first_manifest(env):
    env.s3.objects.pop(state.MANIFEST_KEY)
    wh = env.data / "warehouse"
    make_live(wh / "sattrack.duckdb", tag="laptop")
    make_ops(wh / "sattrack_ops.duckdb", [("run_laptop", "ok", PRIOR_AT)])
    assert state.cmd_seed(argparse.Namespace()) == 0
    m = env.s3.json(state.MANIFEST_KEY)
    assert m["live"]["run_id"] == "run_laptop" and m["last_ok_at"] is None
    assert m["last_run"]["trigger"] == "seed-from-laptop"


def test_seed_refuses_a_build_that_fails_the_integrity_check(env):
    env.s3.objects.pop(state.MANIFEST_KEY)
    wh = env.data / "warehouse"
    make_live(wh / "sattrack.duckdb", gp_rows=0)
    make_ops(wh / "sattrack_ops.duckdb", [("run_laptop", "ok", PRIOR_AT)])
    with pytest.raises(SystemExit, match="integrity check"):
        state.cmd_seed(argparse.Namespace())
    assert state.MANIFEST_KEY not in env.s3.objects

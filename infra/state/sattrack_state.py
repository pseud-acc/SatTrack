"""SatTrack run state in S3: pull before a run, push (promote) after it.  DRAFT - not yet wired or tested.

Design: agents/hosting/hosting_security_plan.html, section "State handling".

Layout in the private bucket (versioning on):
  state/manifest.json            the commit point; every write is conditional (If-Match / If-None-Match)
  warehouse/sattrack.duckdb      live DB, fixed key; the manifest names the exact VersionId that is "good"
  warehouse/sattrack_ops.duckdb  ops DB (Elementary + audit, incl. the Space-Track login backoff counter)
  raw_history/<schema>/<table>/<run_id>.parquet   write-once, expired by a lifecycle rule
  reports/health/*, reports/data_summary.html      latest pages (versioned)
  app/satcat_tle.csv             what the Heroku app reads (fixed keys, versioned)
  app/last_data_update.csv
  app/manifest.json              the export's own manifest (rows, sha256, as-of dates)
  app/current.json               pointer, written LAST: names the exact VersionId + SHA-256 of each CSV
  logs/<run>.log                 the full private run log (never printed to the public Actions log)

Rules (fail closed, keep last good data):
  * pull: no manifest -> exit 1 (state must be seeded once with `seed`); a download whose SHA-256 does
    not match the manifest -> exit 1. Nothing then runs, so Space-Track is never called without the
    persisted login-backoff counter.
  * push: the live DB is promoted only when the pipeline finished (a new audit.pipeline_run row),
    its status is ok/warn and the required marts open with rows. The ops DB is promoted whenever it
    opens cleanly, so failed logins are remembered. The manifest is written with If-Match on the ETag
    read at pull time, so a concurrent run can never overwrite a newer commit.
  * This script prints key names, sizes and statuses only - never data or credentials.

Commands:
  pull  [--force] [--min-hours H]     download state; writes run=true|false to $GITHUB_OUTPUT
  push  --pipeline-exit N [--log-file P]
  seed                                one-time, run by the admin from the laptop (phase 1 cutover)
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

MANIFEST_KEY = "state/manifest.json"
LIVE_KEY = "warehouse/sattrack.duckdb"
OPS_KEY = "warehouse/sattrack_ops.duckdb"
APP_PREFIX = "app/"
APP_POINTER_KEY = "app/current.json"
APP_CSVS = ["satcat_tle.csv", "last_data_update.csv"]   # written by scripts/export_app_csvs.py into DATA_DIR/app/
REQUIRED_MARTS = [("marts", "fct__satellite_master"), ("marts_tracking", "fct__gp_elements")]
PROMOTABLE_STATUSES = {"ok", "warn"}
DUCKDB_STORAGE_VERSION = "v1.4.0"   # keep in step with ingestion/sattrack_ingest/config.py


def log(msg: str) -> None:
    print(f"[state] {msg}", flush=True)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def s3():
    import boto3  # region and credentials come from the environment (configure-aws-credentials)
    return boto3.client("s3")


def bucket() -> str:
    name = os.environ.get("SATTRACK_BUCKET")
    if not name:
        sys.exit("SATTRACK_BUCKET is not set")
    return name


def data_dir() -> Path:
    d = os.environ.get("SATTRACK_DATA_DIR")
    if not d:
        sys.exit("SATTRACK_DATA_DIR is not set")
    return Path(d)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def github_output(**kv) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            for k, v in kv.items():
                f.write(f"{k}={v}\n")


def read_manifest(client):
    """Return (manifest, etag) or (None, None) when no state has been committed yet."""
    from botocore.exceptions import ClientError
    try:
        obj = client.get_object(Bucket=bucket(), Key=MANIFEST_KEY)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None, None
        raise
    return json.loads(obj["Body"].read()), obj["ETag"]


def put_file(client, key: str, path: Path, *, create_only: bool = False) -> dict:
    digest = sha256_file(path)
    extra = {"IfNoneMatch": "*"} if create_only else {}
    with path.open("rb") as body:
        resp = client.put_object(Bucket=bucket(), Key=key, Body=body,
                                 ChecksumSHA256=base64.b64encode(bytes.fromhex(digest)).decode(), **extra)
    log(f"uploaded {key} ({path.stat().st_size:,} bytes)")
    return {"key": key, "version_id": resp.get("VersionId"), "sha256": digest}


def get_version(client, entry: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket(), entry["key"], str(dest), ExtraArgs={"VersionId": entry["version_id"]})
    if sha256_file(dest) != entry["sha256"]:
        dest.unlink(missing_ok=True)
        sys.exit(f"checksum mismatch for {entry['key']} - refusing to run on unverified state")
    log(f"downloaded {entry['key']} ({dest.stat().st_size:,} bytes, verified)")


def duck(path: Path, read_only: bool = True):
    import duckdb
    cfg = {} if read_only else {"storage_compatibility_version": DUCKDB_STORAGE_VERSION}
    return duckdb.connect(str(path), read_only=read_only, config=cfg)


def latest_run(ops_path: Path):
    """(run_id, status) of the newest audit.pipeline_run row, or (None, None)."""
    if not ops_path.exists():
        return None, None
    try:
        with duck(ops_path) as con:
            row = con.execute("select run_id, status from audit.pipeline_run order by started_at desc limit 1").fetchone()
    except Exception as exc:  # noqa: BLE001 - reported by type only
        log(f"ops DB unreadable ({type(exc).__name__})")
        return None, None
    return (row[0], row[1]) if row else (None, None)


def live_db_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with duck(path) as con:
            for schema, table in REQUIRED_MARTS:
                if con.execute(f'select count(*) from {schema}."{table}"').fetchone()[0] <= 0:
                    log(f"integrity: {schema}.{table} is empty")
                    return False
    except Exception as exc:  # noqa: BLE001
        log(f"integrity: live DB check failed ({type(exc).__name__})")
        return False
    return True


def publish_app(client, export: Path, run_id: str, now: datetime) -> None:
    """Publish the export so the app always sees BOTH CSVs from the same run.

    Fixed keys + S3 versioning: each CSV is uploaded (new VersionId), then app/current.json - the pointer - is
    written last, naming the exact VersionId and SHA-256 of each file. The app reads the pointer first and then
    fetches those exact versions, so it can never pair one run's satellites with another run's freshness row.
    A failed or partial upload leaves the old pointer in place; superseded versions stay readable for the
    rollback window (noncurrent-version lifecycle rule), and the current versions never expire.
    """
    try:
        export_manifest = json.loads((export / "manifest.json").read_text(encoding="utf-8"))
        listed = {f["file"]: f for f in export_manifest["files"]}
        for name in APP_CSVS:   # the export's own checksums must match what is on disk
            if name not in listed or sha256_file(export / name) != listed[name]["sha256"]:
                raise ValueError(name)
    except Exception as exc:  # noqa: BLE001 - reported by type only
        log(f"no valid app export ({type(exc).__name__}) - app data left unchanged")
        return
    files = {}
    for name in APP_CSVS:
        entry = put_file(client, APP_PREFIX + name, export / name)
        files[name] = {"key": entry["key"], "version_id": entry["version_id"], "sha256": entry["sha256"],
                       "rows": listed[name]["rows"]}
    put_file(client, APP_PREFIX + "manifest.json", export / "manifest.json")
    pointer = {"schema": 1, "run_id": run_id, "export_run_id": export_manifest.get("run_id"),
               "generated_at": export_manifest.get("generated_at"), "published_at": now.isoformat(),
               "files": files}
    client.put_object(Bucket=bucket(), Key=APP_POINTER_KEY, Body=json.dumps(pointer, indent=1).encode(),
                      ContentType="application/json")
    log("app pointer written (app/current.json)")


# --------------------------------------------------------------------------------------------- commands
def cmd_pull(args) -> int:
    client, d = s3(), data_dir()
    wh = d / "warehouse"
    manifest, etag = read_manifest(client)
    if manifest is None:
        log("no committed state (state/manifest.json missing) - seed it once from the laptop; not running")
        github_output(run="false")
        return 1
    last_ok = manifest.get("last_ok_at")
    if last_ok and not args.force:
        age = utcnow() - datetime.fromisoformat(last_ok)
        if age < timedelta(hours=args.min_hours):
            log(f"last successful run {age.total_seconds() / 3600:.1f} h ago - nothing to do")
            github_output(run="false")
            return 0
    get_version(client, manifest["live"], wh / "sattrack.duckdb")
    get_version(client, manifest["ops"], wh / "sattrack_ops.duckdb")
    prior_run_id, _ = latest_run(wh / "sattrack_ops.duckdb")
    marker = {"etag": etag, "pulled_at": utcnow().isoformat(), "prior_run_id": prior_run_id, "manifest": manifest}
    (d / ".state").mkdir(parents=True, exist_ok=True)
    (d / ".state" / "pull.json").write_text(json.dumps(marker), encoding="utf-8")
    github_output(run="true")
    return 0


def cmd_push(args) -> int:
    client, d = s3(), data_dir()
    wh = d / "warehouse"
    marker = json.loads((d / ".state" / "pull.json").read_text(encoding="utf-8"))
    old = marker["manifest"]
    now = utcnow()
    run_tag = os.environ.get("GITHUB_RUN_ID", now.strftime("%Y%m%dT%H%M%SZ"))

    # Private log first: it is useful even when nothing else is promoted.
    if args.log_file and Path(args.log_file).exists():
        put_file(client, f"logs/{now:%Y/%m/%d}/{run_tag}.log", Path(args.log_file))

    run_id, status = latest_run(wh / "sattrack_ops.duckdb")
    finished = run_id is not None and run_id != marker["prior_run_id"]
    if run_id is None:
        log("ops DB unreadable - committing nothing (last good state stays current)")
        return 1
    promote_live = finished and status in PROMOTABLE_STATUSES and live_db_ok(wh / "sattrack.duckdb")
    log(f"pipeline finished={finished} status={status if finished else 'n/a'} exit={args.pipeline_exit} "
        f"-> promote live={promote_live}")

    # Raw history is write-once per run: upload whatever this run landed (also on a held build).
    raw = d / "raw_history"
    if raw.exists():
        for f in sorted(raw.rglob("*.parquet")):
            put_file(client, "raw_history/" + f.relative_to(raw).as_posix(), f, create_only=True)

    new = dict(old)
    new["ops"] = put_file(client, OPS_KEY, wh / "sattrack_ops.duckdb")
    if promote_live:
        new["live"] = put_file(client, LIVE_KEY, wh / "sattrack.duckdb")
        new["live"]["run_id"] = run_id
        if status == "ok":
            new["last_ok_at"] = now.isoformat()
    new["last_run"] = {"run_id": run_id if finished else None, "status": status if finished else "crashed",
                       "promoted_live": promote_live, "at": now.isoformat(),
                       "github_run_id": os.environ.get("GITHUB_RUN_ID"), "git_sha": os.environ.get("GITHUB_SHA"),
                       "trigger": os.environ.get("SATTRACK_TRIGGER")}

    from botocore.exceptions import ClientError
    try:  # the commit point: compare-and-swap on the ETag read at pull time
        client.put_object(Bucket=bucket(), Key=MANIFEST_KEY, Body=json.dumps(new, indent=1).encode(),
                          ContentType="application/json", IfMatch=marker["etag"])
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        log(f"manifest commit refused ({code}) - another run committed first; this run's uploads are ignored")
        return 1
    log("manifest committed")

    # After the commit: pages and the app data (a failure here leaves the previous app data in place).
    if promote_live:
        for page, key in [(d / "health" / "health.html", "reports/health/health.html"),
                          (d / "health" / "health.json", "reports/health/health.json"),
                          (d / "reports" / "data_summary.html", "reports/data_summary.html")]:
            if page.exists():
                put_file(client, key, page)
        publish_app(client, d / "app", run_id, now)
    return 0 if finished and args.pipeline_exit == 0 else 1


def cmd_seed(args) -> int:
    """One-time cutover from the laptop, run with the admin's own AWS credentials."""
    client, d = s3(), data_dir()
    wh = d / "warehouse"
    manifest, _ = read_manifest(client)
    if manifest is not None:
        sys.exit("state already exists - seed refuses to overwrite it")
    if not live_db_ok(wh / "sattrack.duckdb"):
        sys.exit("local live DB missing or failing the integrity check - not seeding")
    run_id, status = latest_run(wh / "sattrack_ops.duckdb")
    live = put_file(client, LIVE_KEY, wh / "sattrack.duckdb")
    live["run_id"] = run_id
    new = {"schema": 1, "live": live, "ops": put_file(client, OPS_KEY, wh / "sattrack_ops.duckdb"),
           "last_ok_at": None,
           "last_run": {"run_id": run_id, "status": status, "promoted_live": True, "at": utcnow().isoformat(),
                        "trigger": "seed-from-laptop"}}
    client.put_object(Bucket=bucket(), Key=MANIFEST_KEY, Body=json.dumps(new, indent=1).encode(),
                      ContentType="application/json", IfNoneMatch="*")
    log("seeded: manifest created")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("pull")
    pl.add_argument("--force", action="store_true", default=os.environ.get("SATTRACK_FORCE") == "true")
    pl.add_argument("--min-hours", type=float, default=12.0)
    ps = sub.add_parser("push")
    ps.add_argument("--pipeline-exit", type=int, required=True)
    ps.add_argument("--log-file")
    sub.add_parser("seed")
    args = p.parse_args()
    return {"pull": cmd_pull, "push": cmd_push, "seed": cmd_seed}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

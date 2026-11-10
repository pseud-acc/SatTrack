"""Paths and the source registry for SatTrack ingestion.

Every raw table is landed unchanged (all VARCHAR, original column names) plus metadata columns.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("SATTRACK_DATA_DIR", REPO_ROOT / "data"))
WAREHOUSE_DIR = DATA_DIR / "warehouse"
RAW_HISTORY_DIR = DATA_DIR / "raw_history"

LIVE_DB = WAREHOUSE_DIR / "sattrack.duckdb"          # what the app reads; replaced only on success
BUILD_DB = WAREHOUSE_DIR / "sattrack_build.duckdb"   # this run's working copy
OPS_DB = WAREHOUSE_DIR / "sattrack_ops.duckdb"       # permanent: Elementary + audit

# dbt v2's bundled DuckDB driver reads storage versions 64-68 only, while the Python duckdb 2.0 library
# writes "latest" (999) by default. Every Python connection pins a version dbt can read (phase 0 finding).
DUCKDB_STORAGE_VERSION = "v1.4.0"

RAW_HISTORY_RETENTION_DAYS = int(os.environ.get("SATTRACK_RAW_HISTORY_DAYS", "90"))
SPACETRACK_BASE = "https://www.space-track.org"
GCAT_BASE = "https://planet4589.org/space/gcat/tsv"

# Space-Track login backoff (plan section 15.3): stop after this many consecutive failed logins.
SPACETRACK_MAX_CONSECUTIVE_LOGIN_FAILURES = 3


@dataclass(frozen=True)
class GcatFile:
    table: str          # raw table name in schema raw_jsr
    path: str           # path under GCAT_BASE
    doc_url: str        # publisher's column documentation


GCAT_FILES = [
    GcatFile("satcat", "cat/satcat.tsv", "https://planet4589.org/space/gcat/web/cat/cols.html"),
    GcatFile("satcat100k", "cat/satcat100k.tsv", "https://planet4589.org/space/gcat/web/cat/cols.html"),
    GcatFile("psatcat", "cat/psatcat.tsv", "https://planet4589.org/space/gcat/web/cat/pcols.html"),
    GcatFile("psatcat100k", "cat/psatcat100k.tsv", "https://planet4589.org/space/gcat/web/cat/pcols.html"),
    GcatFile("currentcat", "derived/currentcat.tsv", "https://planet4589.org/space/gcat/web/cat/curcols.html"),
    GcatFile("launchlog", "derived/launchlog.tsv", "https://planet4589.org/space/gcat/web/cat/llog.html"),
    GcatFile("orgs", "tables/orgs.tsv", "https://planet4589.org/space/gcat/web/orgs/index.html"),
    GcatFile("sites", "tables/sites.tsv", "https://planet4589.org/space/gcat/web/sites/index.html"),
    GcatFile("lv", "tables/lv.tsv", "https://planet4589.org/space/gcat/web/lvs/lv/index.html"),
]



@dataclass
class RunContext:
    run_id: str
    loaded_at: str                     # ISO UTC timestamp shared by every table in the run
    stage_status: dict = field(default_factory=dict)


def connect(path, read_only: bool = False, retries: int = 6, wait_s: float = 5.0):
    """Open a DuckDB file in a storage format dbt v2 can read.

    Retries when another process briefly holds the file (sync clients, antivirus, an editor);
    phase 0 hit this with Dropbox. Keep SATTRACK_DATA_DIR outside synced folders in any case.
    """
    import time

    import duckdb
    cfg = {} if read_only else {"storage_compatibility_version": DUCKDB_STORAGE_VERSION}
    for attempt in range(retries + 1):
        try:
            return duckdb.connect(str(path), read_only=read_only, config=cfg)
        except duckdb.IOException as exc:
            if "being used by another process" not in str(exc) and "Could not set lock" not in str(exc) or attempt == retries:
                raise
            time.sleep(wait_s)

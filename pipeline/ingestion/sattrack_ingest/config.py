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


# CelesTrak groups (D-026, D-047). CelesTrak is the golden source for constellations and satellite systems: only the
# groups listed here are downloaded, and the dbt models name each grouping by CelesTrak's own title. Every other group
# on CelesTrak's GP index is excluded; the excluded list holds the groups the index showed on 2026-11-22 (fetch run
# 45061938995), so a dbt check can warn (never fail) when the index lists a group that is in no list. Changing a list
# is a config change in a PR, decided against D-047. Kinds:
#   * constellation: near-identical satellites working together (Starlink, OneWeb, ...). Order is precedence: an
#     object in two groups takes the first.
#   * system: a satellite system (non-identical satellites working together). Members whose names don't fit the group
#     are dropped, then GCAT completes the system with every payload of the kept members' programme families.
#   * system_hosted: satellites carrying a system's payload as a guest (Cospas-Sarsat repeaters). A membership,
#     never a satellite's primary system, and never completed from GCAT.
#   * system_hosted_umbrella: a group named after an umbrella term (sbas: "SBAS" covers WAAS, EGNOS, MSAS, GAGAN, ...).
#     Never a system itself: each member's hosted system is the token CelesTrak writes before "/PRN" in its name.
CELESTRAK_CONSTELLATION_GROUPS = [
    "starlink", "oneweb", "kuiper", "qianfan", "hulianwang", "iridium-NEXT", "globalstar", "orbcomm",
]
CELESTRAK_SYSTEM_GROUPS = ["gps-ops", "glo-ops", "galileo", "beidou", "tdrss", "dmc"]
CELESTRAK_SYSTEM_HOSTED_GROUPS = ["sarsat"]
CELESTRAK_SYSTEM_HOSTED_UMBRELLA_GROUPS = ["sbas"]
# Member-name prefix (D-046): a group listed here gives its name only to members whose CelesTrak OBJECT_NAME starts
# with the prefix (case-insensitive); its other members are treated as not in the group. Empty since D-047: tdrss, the
# case it was made for, is a system group now, and system groups keep only members whose names fit the group (their
# most common leading word, TDRS for tdrss). Changing this is a config change in a PR, decided against D-046.
CELESTRAK_MEMBER_NAME_PREFIX: dict[str, str] = {}
# The space station group (D-043): downloaded like the groups above, but it sets flag_space_station and never the
# constellation (the ISS and Tiangong modules plus the spacecraft visiting them are not a constellation).
CELESTRAK_STATION_GROUPS = ["stations"]
CELESTRAK_EXCLUDED_GROUPS = [
    "last-30-days", "visual", "active", "analyst", "fengyun-1c-debris", "iridium-33-debris",
    "cosmos-2251-debris", "weather", "resource", "sar", "argos", "geo", "amateur", "satnogs", "x-comm",
    "other-comm", "science", "geodetic", "engineering", "education", "military", "radar", "cubesat",
    # gnss: "GNSS" is the umbrella term for every navigation system, not a system itself (owner, D-047); it also
    # lists SBAS host satellites. Its systems come from their own groups or the ad-hoc seed (NavIC, QZSS).
    "gnss",
    # D-047: operator fleets are neither constellations nor systems (GCAT gives each satellite's operator)
    "planet", "spire", "intelsat", "ses", "eutelsat", "telesat",
]
# Download cadence (D-039): at most once per CELESTRAK_MIN_HOURS (CelesTrak updates GP every 2 hours, so this
# is well inside "once per update"), and no request at all for CELESTRAK_REFUSAL_COOLDOWN_HOURS after any refusal
# (the policy's 15-minute stop after a 5xx is the minimum; a 403/404/429/301 is not retried the same day either).
CELESTRAK_MIN_HOURS = 20
CELESTRAK_REFUSAL_COOLDOWN_HOURS = 20
CELESTRAK_PAUSE_S = 5.0          # between requests, as in the analysis fetch (#62)


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

"""Extractors: fetch each source and land it raw. Every call is logged to audit.ingestion_call.

Space-Track: one session, GP + boxscore, login backoff so unattended hourly runs can't lock the
account (stop after N consecutive failed logins; the last good tracking data is kept).
GCAT: public TSVs; the '# Updated' row becomes _source_updated_at. GCAT's code tables (mission category,
ownership class) are parsed from its documentation page into raw_jsr.gcat_code_labels on the same schedule.
pycountry: ISO 3166-1 + historic 3166-3, pinned in requirements.
geonames: GeoNames cities15000 and the country list via the pinned geonamescache package.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import requests

from . import audit
from .config import (GCAT_BASE, GCAT_FILES, SPACETRACK_BASE, SPACETRACK_MAX_CONSECUTIVE_LOGIN_FAILURES,
                     RunContext)
from .credentials import resolve_spacetrack_credentials
from .gcat_docs import CODE_LABELS_URL, parse_code_labels
from .raw_writer import land_delimited, land_records

UA = {"User-Agent": "SatTrack-pipeline/0.1 (+https://github.com/pseud-acc/SatTrack)"}
GP_QUERY = "/basicspacedata/query/class/gp/decay_date/null-val/epoch/%3Enow-10/format/json"
BOXSCORE_QUERY = "/basicspacedata/query/class/boxscore/format/json"


class LoginBlocked(RuntimeError):
    pass


# Skip a fetch when the landed copy is younger than this (Space-Track: GP at most hourly, boxscore daily).
MAX_AGE_MINUTES = {"raw_spacetrack.gp": 55, "raw_spacetrack.boxscore": 23 * 60, "raw_jsr": 6 * 60}


def _age_minutes(con, table: str):
    """Minutes since the table was last landed, computed in SQL (no tz-aware values reach Python).
    Returns None when the table doesn't exist or is empty; raises on any other error."""
    exists = con.execute("select count(*) from duckdb_tables() where schema_name || '.' || table_name = ?", [table]).fetchone()[0]
    if not exists:
        return None
    return con.execute(f"select (epoch(now()) - epoch(max(cast(_loaded_at as timestamptz)))) / 60.0 from {table}").fetchone()[0]


def _fresh(con, table: str, limit_key: str, *, fail_safe_skip: bool = False) -> bool:
    """True when the landed copy is younger than the limit. If the age can't be determined and
    fail_safe_skip is set (Space-Track), treat it as fresh: a broken check must never cause extra
    Space-Track queries; it costs stale data instead, which freshness tests and the health page show."""
    try:
        age = _age_minutes(con, table)
    except Exception:  # noqa: BLE001
        return fail_safe_skip
    return age is not None and age < MAX_AGE_MINUTES[limit_key]


def _log_skip(ops, ctx, source, table, url):
    audit.record_call(ops, ctx.run_id, source=source, target_table=table, url=url, started_at=datetime.now(timezone.utc),
                      duration_s=0.0, http_status=None, bytes=0, rows=None, retries=0, flag_skipped_fresh=1, error=None)


def _get(session, url, *, retries=2, timeout=120):
    last = None
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=timeout, headers=UA)
            if r.status_code < 500:
                return r, attempt
            last = f"HTTP {r.status_code}"
        except requests.RequestException as exc:  # network error: retry with backoff
            last = str(exc)
        time.sleep(2 ** attempt * 5)
    raise RuntimeError(f"GET failed after {retries + 1} attempts: {last}")


def ingest_spacetrack(con, ops, ctx: RunContext) -> dict:
    """Return per-table row counts. Raises LoginBlocked when the backoff limit is reached."""
    todo = [(t, q) for t, q in [("gp", GP_QUERY), ("boxscore", BOXSCORE_QUERY)]
            if not _fresh(con, f"raw_spacetrack.{t}", f"raw_spacetrack.{t}", fail_safe_skip=True)]
    for t, q in [("gp", GP_QUERY), ("boxscore", BOXSCORE_QUERY)]:
        if (t, q) not in todo:
            _log_skip(ops, ctx, "spacetrack", f"raw_spacetrack.{t}", SPACETRACK_BASE + q)
    if not todo:
        return {"skipped_fresh": ["gp", "boxscore"]}
    failures = audit.login_failures(ops, "spacetrack")
    if failures >= SPACETRACK_MAX_CONSECUTIVE_LOGIN_FAILURES:
        raise LoginBlocked(f"{failures} consecutive failed logins; not retrying until reset")
    user, password = resolve_spacetrack_credentials()
    out = {}
    with requests.Session() as s:
        t0 = time.time()
        resp = s.post(SPACETRACK_BASE + "/ajaxauth/login", data={"identity": user, "password": password},
                      headers=UA, timeout=60)
        ok = resp.status_code == 200 and "Failed" not in resp.text
        audit.record_login(ops, "spacetrack", ok, None if ok else f"login HTTP {resp.status_code}")
        audit.record_call(ops, ctx.run_id, source="spacetrack", target_table="(login)", url=SPACETRACK_BASE + "/ajaxauth/login",
                          started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                          http_status=resp.status_code, bytes=0, rows=0, retries=0, flag_skipped_fresh=0,
                          error=None if ok else "login failed")
        if not ok:
            raise RuntimeError("Space-Track login failed")
        try:
            for table, query in todo:
                t0 = time.time()
                r, retries = _get(s, SPACETRACK_BASE + query)
                err = None if r.status_code == 200 else f"HTTP {r.status_code}"
                rows = 0
                if r.status_code == 200:
                    records = r.json()
                    rows = land_records(con, ctx, "raw_spacetrack", table, records, source_url=SPACETRACK_BASE + query,
                                        source_updated_at=None, source_file=table)
                    out[table] = rows
                audit.record_call(ops, ctx.run_id, source="spacetrack", target_table=f"raw_spacetrack.{table}",
                                  url=SPACETRACK_BASE + query, started_at=datetime.fromtimestamp(t0, timezone.utc),
                                  duration_s=time.time() - t0, http_status=r.status_code, bytes=len(r.content), rows=rows,
                                  retries=retries, flag_skipped_fresh=0, error=err)
                if err:
                    raise RuntimeError(f"Space-Track {table}: {err}")
        finally:
            s.get(SPACETRACK_BASE + "/ajaxauth/logout", headers=UA, timeout=30)
    return out


_UPDATED = re.compile(r"^#\s*Updated\s+(\d{4} \w{3}\s+\d{1,2})\s+(\d{2})(\d{2}):(\d{2})", re.M)


def _gcat_updated(text: str) -> str | None:
    m = _UPDATED.search(text[:500])
    if not m:
        return None
    d = datetime.strptime(re.sub(r"\s+", " ", m.group(1)), "%Y %b %d")
    return d.replace(hour=int(m.group(2)), minute=int(m.group(3)), second=int(m.group(4)), tzinfo=timezone.utc).isoformat()


def ingest_gcat(con, ops, ctx: RunContext) -> dict:
    out = {}
    with requests.Session() as s:
        for f in GCAT_FILES:
            url = f"{GCAT_BASE}/{f.path}"
            if _fresh(con, f"raw_jsr.{f.table}", "raw_jsr"):
                _log_skip(ops, ctx, "jsr", f"raw_jsr.{f.table}", url)
                out[f.table] = "skipped_fresh"
                continue
            t0 = time.time()
            r, retries = _get(s, url)
            err, rows, updated = None, 0, None
            if r.status_code == 200:
                text = r.content.decode("utf-8", errors="replace")
                updated = _gcat_updated(text)
                lines = text.splitlines()
                header = lines[0].lstrip("#")
                data = [ln for ln in lines[1:] if ln and not ln.startswith("#")]
                rows = land_delimited(con, ctx, "raw_jsr", f.table, "\n".join([header] + data) + "\n", delimiter="\t",
                                      source_url=url, source_updated_at=updated, source_file=f.path.rsplit("/", 1)[-1])
                out[f.table] = rows
            else:
                err = f"HTTP {r.status_code}"
            audit.record_call(ops, ctx.run_id, source="jsr", target_table=f"raw_jsr.{f.table}", url=url,
                              started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                              http_status=r.status_code, bytes=len(r.content), rows=rows, retries=retries,
                              flag_skipped_fresh=0, error=err)
            if err:
                raise RuntimeError(f"GCAT {f.table}: {err}")
        out["gcat_code_labels"] = _ingest_gcat_code_labels(con, ops, ctx, s)
    return out


def _ingest_gcat_code_labels(con, ops, ctx: RunContext, session):
    """GCAT's code meanings, parsed from its documentation page (gcat_docs.py). A layout change raises,
    so the enrichment unit keeps its last good build instead of losing labels."""
    table = "raw_jsr.gcat_code_labels"
    if _fresh(con, table, "raw_jsr"):
        _log_skip(ops, ctx, "jsr", table, CODE_LABELS_URL)
        return "skipped_fresh"
    t0 = time.time()
    r, retries = _get(session, CODE_LABELS_URL)
    err, rows = None, 0
    if r.status_code == 200:
        try:
            records = parse_code_labels(r.content.decode("latin-1"))
            rows = land_records(con, ctx, "raw_jsr", "gcat_code_labels", records, source_url=CODE_LABELS_URL,
                                source_updated_at=None, source_file="pcols.html")
        except Exception as exc:  # noqa: BLE001 - recorded, then raised so the unit is held
            err = f"parse: {exc}"
    else:
        err = f"HTTP {r.status_code}"
    audit.record_call(ops, ctx.run_id, source="jsr", target_table=table, url=CODE_LABELS_URL,
                      started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                      http_status=r.status_code, bytes=len(r.content), rows=rows, retries=retries,
                      flag_skipped_fresh=0, error=err)
    if err:
        raise RuntimeError(f"GCAT code labels: {err}")
    return rows


def ingest_pycountry(con, ops, ctx: RunContext) -> dict:
    import importlib.metadata as md

    import pycountry
    t0 = time.time()
    rows = []
    for c in pycountry.countries:
        rows.append({"alpha_2": c.alpha_2, "alpha_3": c.alpha_3, "numeric": c.numeric, "name": c.name,
                     "official_name": getattr(c, "official_name", None), "common_name": getattr(c, "common_name", None),
                     "alpha_4": None, "withdrawal_date": None, "is_historic": "false"})
    for c in pycountry.historic_countries:
        rows.append({"alpha_2": getattr(c, "alpha_2", None), "alpha_3": getattr(c, "alpha_3", None),
                     "numeric": getattr(c, "numeric", None), "name": c.name, "official_name": None, "common_name": None,
                     "alpha_4": getattr(c, "alpha_4", None), "withdrawal_date": getattr(c, "withdrawal_date", None),
                     "is_historic": "true"})
    ver = md.version("pycountry")
    n = land_records(con, ctx, "raw_pycountry", "iso_countries", rows, source_url=f"pycountry=={ver}",
                     source_updated_at=None, source_file=f"pycountry-{ver}")
    audit.record_call(ops, ctx.run_id, source="pycountry", target_table="raw_pycountry.iso_countries", url=f"pycountry=={ver}",
                      started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                      http_status=None, bytes=0, rows=n, retries=0, flag_skipped_fresh=0, error=None)
    return {"iso_countries": n}


def ingest_geonames(con, ops, ctx: RunContext) -> dict:
    """GeoNames cities and countries (pinned geonamescache, offline): cities locate launch sites; country names
    are the second step of the owner-country name match (after ISO 3166-1, before ISO 3166-3)."""
    import importlib.metadata as md

    import geonamescache
    t0 = time.time()
    gver = md.version("geonamescache")
    gc = geonamescache.GeonamesCache()
    cities = [{"geonameid": c["geonameid"], "name": c["name"], "countrycode": c["countrycode"],
               "latitude": c["latitude"], "longitude": c["longitude"], "population": c["population"]}
              for c in gc.get_cities().values()]
    n = land_records(con, ctx, "raw_geonames", "cities", cities, source_url=f"geonamescache=={gver}",
                     source_updated_at=None, source_file=f"geonamescache-{gver}")
    audit.record_call(ops, ctx.run_id, source="geonames", target_table="raw_geonames.cities", url=f"geonamescache=={gver}",
                      started_at=datetime.fromtimestamp(t0, timezone.utc), duration_s=time.time() - t0,
                      http_status=None, bytes=0, rows=n, retries=0, flag_skipped_fresh=0, error=None)
    t1 = time.time()
    countries = [{"geonameid": c["geonameid"], "name": c["name"], "iso": c["iso"], "iso3": c["iso3"]}
                 for c in gc.get_countries().values()]
    n_countries = land_records(con, ctx, "raw_geonames", "countries", countries, source_url=f"geonamescache=={gver}",
                               source_updated_at=None, source_file=f"geonamescache-{gver}")
    audit.record_call(ops, ctx.run_id, source="geonames", target_table="raw_geonames.countries", url=f"geonamescache=={gver}",
                      started_at=datetime.fromtimestamp(t1, timezone.utc), duration_s=time.time() - t1,
                      http_status=None, bytes=0, rows=n_countries, retries=0, flag_skipped_fresh=0, error=None)
    return {"cities": n, "countries": n_countries}

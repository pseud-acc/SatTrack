"""Download CelesTrak's GP group lists once, for analysis and local testing (run by .github/workflows/celestrak-fetch.yml).

    python pipeline/scripts/celestrak_fetch.py <out dir> [--groups a,b,c] [--pause 5]
    python pipeline/scripts/celestrak_fetch.py <out dir> --pages usage-policy.php     (pages only, no groups)

Lists the groups linked from CelesTrak's GP index page, then downloads each group once as CSV, in order, with a pause
between requests. Follows D-008 and CelesTrak's usage policy (updated 2026-11-16): any non-200 response, redirects included, or a
body that isn't CSV stops the whole run (no retries, no further requests); what was fetched so far is kept. Writes <group>.csv per group and manifest.json
(source URLs, statuses, row counts, times). Standard library only. Never run from a machine whose IP CelesTrak has
blocked; the workflow runs it on GitHub's runners.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

INDEX_URL = "https://celestrak.org/NORAD/elements/"
GROUP_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=csv"
USER_AGENT = "SatTrack-analysis/1.0 (+https://github.com/pseud-acc/SatTrack)"
CSV_HEADER = "OBJECT_NAME,"
SITE = "https://celestrak.org/"


class Refused(Exception):
    """CelesTrak refused or returned something unexpected: stop the run (D-008)."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """CelesTrak's usage policy: stop on any non-200 response, redirects (301) included; never follow them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _open(request, timeout):
    return _OPENER.open(request, timeout=timeout)


def get(url: str, opener=_open) -> str:
    # The usage policy asks for compressed downloads; gzip is in the standard library.
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    try:
        with opener(request, timeout=60) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise Refused(f"HTTP {status} for {url}")
            body = response.read()
            headers = getattr(response, "headers", None)
            if headers is not None and headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            return body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise Refused(f"HTTP {e.code} for {url}") from None


def groups_on_index(html: str) -> list[str]:
    """Group names linked from the GP index page, in page order, without duplicates."""
    return list(dict.fromkeys(re.findall(r"gp\.php\?GROUP=([A-Za-z0-9_-]+)", html)))


def check_csv(body: str, url: str) -> int:
    """Number of data rows; raise Refused if the body isn't GP CSV (an HTML or plain-text message)."""
    if not body.startswith(CSV_HEADER):
        raise Refused(f"not CSV from {url}: {body[:80]!r}")
    return max(0, len(body.strip().splitlines()) - 1)


def run(out: Path, wanted: list[str] | None, pause: float, opener=_open, sleep=time.sleep) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"index_url": INDEX_URL, "started_at": datetime.now(timezone.utc).isoformat(), "groups": [],
                "stopped": None}
    try:
        listed = groups_on_index(get(INDEX_URL, opener))
        manifest["groups_on_index"] = listed
        todo = [g for g in listed if wanted is None or g in wanted]
        manifest["not_on_index"] = sorted(set(wanted or []) - set(listed))
        for group in todo:
            sleep(pause)
            url = GROUP_URL.format(group=group)
            body = get(url, opener)
            rows = check_csv(body, url)
            (out / f"{group}.csv").write_text(body, encoding="utf-8")
            manifest["groups"].append({"group": group, "url": url, "rows": rows,
                                       "fetched_at": datetime.now(timezone.utc).isoformat()})
    except Refused as e:
        manifest["stopped"] = str(e)
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def save_pages(out: Path, pages: list[str], pause: float, opener=_open, sleep=time.sleep) -> dict:
    """Archive a few CelesTrak pages (e.g. the usage policy) as HTML, with the same stop-on-refusal rule."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"pages": [], "stopped": None, "started_at": datetime.now(timezone.utc).isoformat()}
    try:
        for i, page in enumerate(pages):
            if not re.fullmatch(r"[A-Za-z0-9_./-]+", page) or ".." in page:
                raise ValueError(f"bad page path: {page!r}")
            if i:
                sleep(pause)
            url = SITE + page
            body = get(url, opener)
            name = page.replace("/", "_")
            (out / name).write_text(body, encoding="utf-8")
            manifest["pages"].append({"page": page, "url": url, "bytes": len(body.encode()),
                                      "fetched_at": datetime.now(timezone.utc).isoformat()})
    except Refused as e:
        manifest["stopped"] = str(e)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("--groups", help="comma-separated group names; default: every group on the index page")
    parser.add_argument("--pause", type=float, default=5.0, help="seconds between requests (default 5)")
    parser.add_argument("--pages", help="comma-separated page paths under celestrak.org to archive instead of groups")
    args = parser.parse_args(argv)
    if args.pages:
        m = save_pages(args.out, [p.strip() for p in args.pages.split(",") if p.strip()], args.pause)
        print(f"{len(m['pages'])} pages; stopped: {m['stopped']}")
        return 1 if m["stopped"] else 0
    wanted = [g.strip() for g in args.groups.split(",") if g.strip()] if args.groups else None
    m = run(args.out, wanted, args.pause)
    print(f"{len(m['groups'])} groups, {sum(g['rows'] for g in m['groups'])} rows; stopped: {m['stopped']}")
    return 1 if m["stopped"] else 0


if __name__ == "__main__":
    sys.exit(main())

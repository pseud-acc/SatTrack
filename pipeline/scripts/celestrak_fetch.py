"""Download CelesTrak's GP group lists once, for analysis and local testing (run by .github/workflows/celestrak-fetch.yml).

    python pipeline/scripts/celestrak_fetch.py <out dir> [--groups a,b,c] [--pause 5]

Lists the groups linked from CelesTrak's GP index page, then downloads each group once as CSV, in order, with a pause
between requests. Follows D-008: a 403, a 429, an error status or a body that isn't CSV stops the whole run (no
retries, no further requests); what was fetched so far is kept. Writes <group>.csv per group and manifest.json
(source URLs, statuses, row counts, times). Standard library only. Never run from a machine whose IP CelesTrak has
blocked; the workflow runs it on GitHub's runners.
"""
from __future__ import annotations

import argparse
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


class Refused(Exception):
    """CelesTrak refused or returned something unexpected: stop the run (D-008)."""


def get(url: str, opener=urllib.request.urlopen) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace")
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


def run(out: Path, wanted: list[str] | None, pause: float, opener=urllib.request.urlopen, sleep=time.sleep) -> dict:
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("--groups", help="comma-separated group names; default: every group on the index page")
    parser.add_argument("--pause", type=float, default=5.0, help="seconds between requests (default 5)")
    args = parser.parse_args(argv)
    wanted = [g.strip() for g in args.groups.split(",") if g.strip()] if args.groups else None
    m = run(args.out, wanted, args.pause)
    print(f"{len(m['groups'])} groups, {sum(g['rows'] for g in m['groups'])} rows; stopped: {m['stopped']}")
    return 1 if m["stopped"] else 0


if __name__ == "__main__":
    sys.exit(main())

"""Download CelesTrak's GP group lists once, for analysis and local testing (run by .github/workflows/celestrak-fetch.yml).

    python pipeline/scripts/celestrak_fetch.py <out dir> [--groups a,b,c] [--pause 5]
    python pipeline/scripts/celestrak_fetch.py <out dir> --pages usage-policy.php     (pages only, no groups)

Lists the groups linked from CelesTrak's GP index page, then downloads each group once as CSV, in order, with a pause
between requests. Follows D-008 and CelesTrak's usage policy (updated 2026-11-16): any non-200 response, redirects included, or a
body that isn't CSV stops the whole run (no retries, no further requests); what was fetched so far is kept. Writes
index.html (the GP index page), <group>.csv per group and manifest.json
(source URLs, statuses, row counts, times). Standard library only (HTTP rules in sattrack_ingest/celestrak.py). Never run from a machine whose IP CelesTrak has
blocked; the workflow runs it on GitHub's runners.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingestion"))
# The HTTP rules live in the shared client (also used by the pipeline's constellation groups, D-026).
from sattrack_ingest.celestrak import (GROUP_URL, INDEX_URL, SITE, Refused, _open, check_csv,  # noqa: E402,F401
                                       groups_on_index)
from sattrack_ingest.celestrak import get as _get  # noqa: E402

USER_AGENT = "SatTrack-analysis/1.0 (+https://github.com/pseud-acc/SatTrack)"


def get(url: str, opener=_open) -> str:
    return _get(url, opener, user_agent=USER_AGENT)


def run(out: Path, wanted: list[str] | None, pause: float, opener=_open, sleep=time.sleep) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"index_url": INDEX_URL, "started_at": datetime.now(timezone.utc).isoformat(), "groups": [],
                "stopped": None}
    try:
        index_html = get(INDEX_URL, opener)
        (out / "index.html").write_text(index_html, encoding="utf-8")   # kept so the title parser can be checked
        listed = groups_on_index(index_html)
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

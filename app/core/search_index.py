"""The satellite search list (D-052; roadmap 3.9's browsable list, built early): GET /data/search.json.

Owner, 27 Nov 2026: the two search dropdowns carried ~19,800 names and ~19,800 SATCAT numbers in the page, and Dash 4's
dropdown indexed them all in the browser (5 s of main-thread time in the first 30 s on a 4x-slowed CPU). Users include
children and casual visitors, so search must stay browsable (owner, 24 Nov 2026), not type-to-search only.

The app derives this dataset from the objects dataset it already holds (same run), at start-up, and serves it like a
published dataset (app/core/data_files.py: Brotli or gzip, ETag, revalidated). The page's search list
(assets/07_search.js) fetches it once, after the globe's first positions, and filters it in the browser.

Records keep the objects dataset's field names (one self-describing record per object, no lookup tables), in the
order the list shows them: space stations first, then payloads, then rocket bodies and debris; within each, objects
Space-Track has named before those it hasn't, then the newest launches first (then the highest SATCAT number), so
browsing starts with what's new. UNKNOWN objects (Space-Track's analyst objects) are left out: the globe never shows
them (D-011). An object not yet named carries Space-Track's placeholder name (UNNAMED); the list shows it by its
international designator (`object_id`) instead.
"""
import gzip
import json

import brotli

FIELDS = ["satcat_id", "object_name", "object_id", "object_type", "operational_status", "launch_year",
          "flag_space_station"]
TYPE_ORDER = {"PAYLOAD": 0, "ROCKET BODY": 1, "DEBRIS": 2}
UNNAMED = "TBA - TO BE ASSIGNED"   # Space-Track's name for an object it hasn't named yet (D-011)


def _order(r):
    year = r.get("launch_year")
    return (0 if r.get("flag_space_station") == 1 else 1, TYPE_ORDER[r["object_type"]],
            1 if r.get("object_name") == UNNAMED else 0,
            -(year if isinstance(year, (int, float)) else 0), -int(r["satcat_id"]))


def search_records(objects_records):
    """The search list's records, in the order the list shows them."""
    rows = [{f: r.get(f) for f in FIELDS} for r in objects_records
            if r.get("satcat_id") is not None and r.get("object_type") in TYPE_ORDER]
    for r in rows:
        if isinstance(r["launch_year"], float):
            r["launch_year"] = int(r["launch_year"])
    return sorted(rows, key=_order)


def search_dataset(objects_doc):
    """The search dataset as the app serves it: {encoding: bytes} (Brotli and gzip). Its envelope is the objects
    dataset's (run, generated time, attribution and the conjunction caution: the names come from Space-Track and
    GCAT), with its own name and count."""
    records = search_records(objects_doc["records"])
    envelope = {k: objects_doc.get(k) for k in ("generated_at", "run_id", "attribution", "caution")}
    body = json.dumps({"dataset": "search", "derived_from": "objects", **envelope, "key": "satcat_id",
                       "count": len(records), "records": records},
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {"br": brotli.compress(body, quality=9), "gzip": gzip.compress(body, 6)}

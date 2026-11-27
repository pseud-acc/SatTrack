"""The satellite search list (app/core/search_index.py; D-052): /data/search.json, derived from the objects dataset.

Scope: one record per object with the objects dataset's own field names; browsing order (space stations, then
payloads, then other types; newest launches first within each); the objects envelope's attribution and caution; served
compressed with an ETag like the published datasets. Expected values come from the objects dataset read directly
(json + gzip), not from the app's helpers.
"""
import gzip
import json
from pathlib import Path

import brotli

from app.core.search_index import FIELDS, search_dataset

SAMPLE = Path(__file__).resolve().parents[1] / "app_data" / "objects.json.gz"


def objects_doc():
    return json.loads(gzip.decompress(SAMPLE.read_bytes()))


def test_one_record_per_object_with_the_objects_field_names():
    doc = objects_doc()
    out = json.loads(gzip.decompress(search_dataset(doc)["gzip"]))
    assert out["dataset"] == "search" and out["derived_from"] == "objects" and out["key"] == "satcat_id"
    shown = [r for r in doc["records"] if r["object_type"] in ("PAYLOAD", "ROCKET BODY", "DEBRIS")]
    assert len(shown) < len(doc["records"]), "the sample has UNKNOWN objects, which the list leaves out (D-011)"
    assert out["count"] == len(out["records"]) == len(shown)
    assert {r["satcat_id"] for r in out["records"]} == {r["satcat_id"] for r in shown}
    assert all(list(r) == FIELDS for r in out["records"])
    by_id = {r["satcat_id"]: r for r in doc["records"]}
    for r in out["records"]:
        src = by_id[r["satcat_id"]]
        assert r["object_name"] == src["object_name"] and r["object_type"] == src["object_type"]
        assert r["object_id"] == src.get("object_id")


def test_attribution_and_caution_travel_with_the_names():
    doc = objects_doc()
    out = json.loads(brotli.decompress(search_dataset(doc)["br"]))
    assert out["attribution"] == doc["attribution"] and out["caution"] == doc["caution"]
    assert out["run_id"] == doc["run_id"]


def test_browsing_order_stations_then_payloads_newest_first():
    doc = objects_doc()
    # Mark one old payload as a station so the sample (which has none) exercises the rule
    oldest = min((r for r in doc["records"] if r["object_type"] == "PAYLOAD" and r.get("launch_year")),
                 key=lambda r: r["launch_year"])
    oldest["flag_space_station"] = 1
    recs = json.loads(gzip.decompress(search_dataset(doc)["gzip"]))["records"]
    assert recs[0]["satcat_id"] == oldest["satcat_id"]
    rank = {"PAYLOAD": 0, "ROCKET BODY": 1, "DEBRIS": 2}
    types = [rank.get(r["object_type"], 3) for r in recs[1:]]
    assert types == sorted(types)
    payload_years = [r["launch_year"] or 0 for r in recs[1:] if r["object_type"] == "PAYLOAD"]
    assert payload_years == sorted(payload_years, reverse=True)


def test_served_compressed_with_an_etag(client):
    resp = client.get("/data/search.json", headers={"Accept-Encoding": "br"})
    assert resp.status_code == 200 and resp.headers["Content-Encoding"] == "br"
    body = json.loads(brotli.decompress(resp.data))
    assert body["dataset"] == "search" and body["count"] == sum(
        r["object_type"] != "UNKNOWN" for r in objects_doc()["records"])
    again = client.get("/data/search.json", headers={"Accept-Encoding": "br", "If-None-Match": resp.headers["ETag"]})
    assert again.status_code == 304


def test_unnamed_objects_come_after_named_ones():
    """Space-Track's placeholder name (owner, 27 Nov 2026: "TBA - TO BE ASSIGNED" topped the list, as the newest
    launches): within a type, named objects first, then those not yet named, each newest first."""
    doc = objects_doc()
    payloads = [r for r in doc["records"] if r["object_type"] == "PAYLOAD"]
    newest = max(payloads, key=lambda r: (r.get("launch_year") or 0, r["satcat_id"]))
    newest["object_name"] = "TBA - TO BE ASSIGNED"
    recs = json.loads(gzip.decompress(search_dataset(doc)["gzip"]))["records"]
    p = [r for r in recs if r["object_type"] == "PAYLOAD" and r["flag_space_station"] != 1]
    assert p[-1]["satcat_id"] == newest["satcat_id"]
    assert all(r["object_name"] != "TBA - TO BE ASSIGNED" for r in p[:-1])

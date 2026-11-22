"""Integration tests: the browser data files (app/core/data_files.py; docs/app-data-contract.md; D-010, D-012).

The app serves each dataset the pipeline published exactly as compressed (Brotli, else gzip, else decompressed),
with an ETag for revalidation. Data: tests/app_data/objects.json.{br,gz}, a 384-record cut of the 21 Nov export.
The slow-client behaviour of the threaded workers is checked against the real Procfile in CI's Heroku build check.
"""
import gzip
import json
from pathlib import Path

import brotli
import pytest

from _support import APP_DATA_DIR, REPO_ROOT

URL = "/data/objects.json"


@pytest.fixture(scope="module")
def sample_objects():
    """The sample dataset, decoded from the committed gzip copy (independent of the app's code)."""
    return json.loads(gzip.decompress((APP_DATA_DIR / "objects.json.gz").read_bytes()))


def test_brotli_when_accepted(client, sample_objects):
    r = client.get(URL, headers={"Accept-Encoding": "gzip, deflate, br"})
    assert r.status_code == 200 and r.headers["Content-Encoding"] == "br"
    assert r.headers["Content-Type"].startswith("application/json")
    assert r.data == (APP_DATA_DIR / "objects.json.br").read_bytes()          # sent as published, not recompressed
    assert json.loads(brotli.decompress(r.data)) == sample_objects


def test_gzip_when_brotli_is_not_accepted(client, sample_objects):
    r = client.get(URL, headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and r.headers["Content-Encoding"] == "gzip"
    assert json.loads(gzip.decompress(r.data)) == sample_objects


def test_uncompressed_when_nothing_is_accepted(client, sample_objects):
    r = client.get(URL, headers={"Accept-Encoding": "identity"})
    assert r.status_code == 200 and "Content-Encoding" not in r.headers
    assert json.loads(r.data) == sample_objects


def test_etag_revalidation_returns_304(client):
    """A browser that already has this run's file downloads nothing; the ETag differs per encoding."""
    first = client.get(URL, headers={"Accept-Encoding": "br"})
    etag = first.headers["ETag"]
    again = client.get(URL, headers={"Accept-Encoding": "br", "If-None-Match": etag})
    assert again.status_code == 304 and again.data == b"" and again.headers["ETag"] == etag
    gz = client.get(URL, headers={"Accept-Encoding": "gzip", "If-None-Match": etag})
    assert gz.status_code == 200 and gz.headers["ETag"] != etag


@pytest.mark.parametrize("validator", ["W/{etag}", "*", '"other", {etag}'])   # {etag} is the quoted header value
def test_if_none_match_uses_weak_comparison(client, validator):
    """RFC 9110 13.1.2 (Copilot review on #58): a weak validator for the current ETag, or '*', also gets 304."""
    etag = client.get(URL, headers={"Accept-Encoding": "br"}).headers["ETag"]
    r = client.get(URL, headers={"Accept-Encoding": "br", "If-None-Match": validator.format(etag=etag)})
    assert r.status_code == 304 and r.data == b""


def test_a_different_etag_gets_the_file(client):
    r = client.get(URL, headers={"Accept-Encoding": "br", "If-None-Match": '"not-this-run"'})
    assert r.status_code == 200 and len(r.data) > 0


@pytest.mark.parametrize("header", ["br;q=0, gzip;q=0, identity;q=0", "*;q=0", "gzip;q=0, identity;q=0"])
def test_406_when_every_representation_is_refused(client, header):
    """RFC 9110 12.5.3 (Copilot review on #58): refusing br, gzip and identity gets 406, not an uncompressed body."""
    r = client.get(URL, headers={"Accept-Encoding": header})
    assert r.status_code == 406 and "Content-Encoding" not in r.headers


def test_cache_headers(client):
    r = client.get(URL, headers={"Accept-Encoding": "br"})
    assert r.headers["Cache-Control"] == "no-cache"        # always revalidate, so new data shows after a run
    assert "Accept-Encoding" in r.headers["Vary"]


def test_unknown_dataset_is_404(client):
    assert client.get("/data/not_a_dataset.json").status_code == 404


def test_the_sample_follows_the_contract(sample_objects):
    """The committed sample has the envelope and keeps every object type (D-011). The pipeline validates the full
    JSON Schema; here the parts the app relies on are checked without the pipeline's validator."""
    d = sample_objects
    assert d["dataset"] == "objects" and d["schema"] == 1 and d["key"] == "satcat_id"
    assert d["count"] == len(d["records"])
    ids = [r["satcat_id"] for r in d["records"]]
    assert ids == sorted(set(ids))
    assert {r["object_type"] for r in d["records"]} == {"PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"}
    schema = json.loads((REPO_ROOT / "app" / "contracts" / "objects.schema.json").read_text(encoding="utf-8"))
    required = schema["$defs"]["record"]["required"]
    assert all(list(r) == required for r in d["records"])                      # same fields, same order
    assert all(isinstance(r["mission_category_labels"], list) for r in d["records"])


@pytest.mark.parametrize("header, available, expected", [
    ("gzip, deflate, br", {"br", "gzip"}, "br"),
    ("br;q=0, gzip", {"br", "gzip"}, "gzip"),
    ("gzip;q=1, br;q=0.5", {"br", "gzip"}, "gzip"),           # the client's preference wins
    ("gzip;q=0", {"br", "gzip"}, "identity"),                 # identity unlisted: acceptable
    ("*", {"br", "gzip"}, "br"),
    ("br", {"gzip"}, "identity"),
    ("", {"br", "gzip"}, "identity"),                         # empty: no coding wanted
    (None, {"br", "gzip"}, "identity"),                       # no header
    ("identity", {"br", "gzip"}, "identity"),
    ("br;q=0, gzip;q=0, identity;q=0", {"br", "gzip"}, None),  # nothing acceptable: 406
    ("*;q=0", {"br", "gzip"}, None),
    ("*;q=0, identity", {"br", "gzip"}, "identity"),
    ("gzip;q=abc", {"br", "gzip"}, "identity"),               # malformed q counts as 0
])
def test_choose_encoding(header, available, expected):
    from app.core.data_files import choose_encoding
    assert choose_encoding(header, available) == expected


def test_a_data_folder_without_datasets_still_loads(tmp_path):
    """An older export (CSVs only) loads with no datasets: the app works and /data/... returns 404."""
    from app.core.state import read_app_csvs_from_dir
    for name in ("satcat_tle.csv", "last_data_update.csv"):
        (tmp_path / name).write_bytes((APP_DATA_DIR / name).read_bytes())
    satcat, metadata, datasets = read_app_csvs_from_dir(str(tmp_path))
    assert len(satcat) > 0 and datasets == {}


def test_procfile_runs_threaded_workers():
    """D-012: the objects file is larger than Heroku's 1 MB router buffer, so workers must be threaded or a slow
    download blocks a whole worker. CI's Heroku build check exercises this with real slow clients."""
    web = (REPO_ROOT / "Procfile").read_text(encoding="utf-8").strip()
    assert web.startswith("web: gunicorn run_app:server") and "--threads" in web.split()

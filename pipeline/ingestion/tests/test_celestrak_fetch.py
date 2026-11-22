"""Unit tests: scripts/celestrak_fetch.py with a fake opener (no network). It must stop at the first refusal or
non-CSV body (D-008), never retry, and pause between requests."""
from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("celestrak_fetch", PIPELINE / "scripts" / "celestrak_fetch.py")
cf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf)

INDEX = ('<a href="gp.php?GROUP=stations&FORMAT=tle">x</a> <a href="gp.php?GROUP=starlink&FORMAT=tle">y</a>'
         '<a href="gp.php?GROUP=starlink&FORMAT=json">dup</a> <a href="gp.php?GROUP=oneweb&FORMAT=tle">z</a>')
CSV = "OBJECT_NAME,OBJECT_ID,NORAD_CAT_ID\nISS (ZARYA),1998-067A,25544\nCSS (TIANHE),2021-035A,48274\n"


class Fake:
    """Answers URLs from a dict; an int value is an HTTP error status. Records every request."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, request, timeout):
        url = request.full_url
        self.calls.append(url)
        answer = self.answers[url]
        if isinstance(answer, int):
            raise urllib.error.HTTPError(url, answer, "refused", {}, None)
        return io.BytesIO(answer.encode())


def group_url(g):
    return cf.GROUP_URL.format(group=g)


def test_index_lists_each_group_once_in_order():
    assert cf.groups_on_index(INDEX) == ["stations", "starlink", "oneweb"]


def test_fetches_every_group_with_a_pause_and_writes_a_manifest(tmp_path):
    fake = Fake({cf.INDEX_URL: INDEX, group_url("stations"): CSV, group_url("starlink"): CSV,
                 group_url("oneweb"): CSV})
    pauses = []
    m = cf.run(tmp_path, None, 5, opener=fake, sleep=pauses.append)
    assert [g["group"] for g in m["groups"]] == ["stations", "starlink", "oneweb"]
    assert [g["rows"] for g in m["groups"]] == [2, 2, 2]
    assert pauses == [5, 5, 5]
    assert m["stopped"] is None
    assert (tmp_path / "starlink.csv").read_text() == CSV
    assert json.loads((tmp_path / "manifest.json").read_text())["groups_on_index"] == ["stations", "starlink", "oneweb"]


def test_only_requested_groups_and_reports_unknown_names(tmp_path):
    fake = Fake({cf.INDEX_URL: INDEX, group_url("oneweb"): CSV})
    m = cf.run(tmp_path, ["oneweb", "kuiper"], 0, opener=fake, sleep=lambda s: None)
    assert fake.calls == [cf.INDEX_URL, group_url("oneweb")]
    assert m["not_on_index"] == ["kuiper"]


def test_a_refusal_stops_the_run_without_retrying(tmp_path):
    fake = Fake({cf.INDEX_URL: INDEX, group_url("stations"): CSV, group_url("starlink"): 403})
    m = cf.run(tmp_path, None, 0, opener=fake, sleep=lambda s: None)
    assert fake.calls == [cf.INDEX_URL, group_url("stations"), group_url("starlink")]   # oneweb never requested
    assert "HTTP 403" in m["stopped"]
    assert [g["group"] for g in m["groups"]] == ["stations"]


def test_a_non_csv_body_stops_the_run(tmp_path):
    fake = Fake({cf.INDEX_URL: INDEX, group_url("stations"): "GP data has not updated since your last download"})
    m = cf.run(tmp_path, None, 0, opener=fake, sleep=lambda s: None)
    assert m["stopped"].startswith("not CSV")
    assert len(fake.calls) == 2
    assert not (tmp_path / "stations.csv").exists()


def test_main_exits_non_zero_when_stopped(tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "run", lambda out, wanted, pause: {"groups": [], "stopped": "HTTP 429"})
    assert cf.main([str(tmp_path)]) == 1


def test_pages_mode_archives_pages_only(tmp_path):
    fake = Fake({cf.SITE + "usage-policy.php": "<html>policy</html>"})
    m = cf.save_pages(tmp_path, ["usage-policy.php"], 5, opener=fake, sleep=lambda s: None)
    assert fake.calls == [cf.SITE + "usage-policy.php"]          # no index page, no groups
    assert (tmp_path / "usage-policy.php").read_text() == "<html>policy</html>"
    assert m["stopped"] is None


def test_pages_mode_stops_on_refusal_and_rejects_odd_paths(tmp_path):
    fake = Fake({cf.SITE + "a.php": 403, cf.SITE + "b.php": "x"})
    m = cf.save_pages(tmp_path, ["a.php", "b.php"], 0, opener=fake, sleep=lambda s: None)
    assert fake.calls == [cf.SITE + "a.php"] and "HTTP 403" in m["stopped"]
    import pytest
    with pytest.raises(ValueError):
        cf.save_pages(tmp_path, ["../etc"], 0, opener=fake, sleep=lambda s: None)

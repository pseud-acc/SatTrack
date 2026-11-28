"""Page tests: the home page and the Explore, Sources and FAQ pages (D-059), through the router callback
(/_dash-update-component), on the sample data.

Scope: every figure on the pages is the sample's own, worked out here with plain pandas from the sample's datasets
(never with the app's summary code); the agreed hero wording; every link on the pages leads to a page the router
knows, the tracker, or an external publisher; the Explore pages rank working satellites; the FAQ's six answers; the
credits and the conjunction caution; no claim the app can't back ("open source" waits for the licence task, 3.7).
"""
import gzip
import json
import re

import pandas as pd
import pytest

from _support import APP_DATA_DIR, objects_sample
from app.callbacks.callback_navbar import page_for
from app.core.catalogue_summary import VIEWS
from app.layouts.components.filters.orbit_filter import ORBIT_HELP


def text(children):
    if children is None:
        return ""
    if isinstance(children, (str, int, float)):
        return str(children)
    if isinstance(children, list):
        return " ".join(text(c) for c in children)
    return text(children.get("props", {}).get("children"))


def walk(node):
    if isinstance(node, list):
        for c in node:
            yield from walk(c)
    elif isinstance(node, dict):
        yield node
        yield from walk(node.get("props", {}).get("children"))


def page(callbacks, path):
    status, out = callbacks.call("page-content", "url.pathname", **{"url.pathname": path})
    assert status == 200
    return out["page-content.children"]


def by_id(tree, cid):
    return next(n for n in walk(tree) if n.get("props", {}).get("id") == cid)


def links(tree):
    return [n["props"]["href"] for n in walk(tree) if isinstance(n.get("props", {}).get("href"), str)]


@pytest.fixture(scope="module")
def objects():
    return objects_sample()


@pytest.fixture(scope="module")
def details():
    doc = json.loads(gzip.decompress((APP_DATA_DIR / "object_detail.json.gz").read_bytes()))
    return pd.DataFrame.from_records(doc["records"])


@pytest.fixture(scope="module")
def working(objects):
    return objects[(objects["object_type"] == "PAYLOAD") & (objects["operational_status"] == "Active")]


def test_hero_states_the_samples_own_numbers_in_the_agreed_words(callbacks, objects, working):
    home = page(callbacks, "/")
    assert text(by_id(home, "home-title")) == f"{len(objects):,} tracked objects in Earth orbit."
    assert text(by_id(home, "home-lede")) == (
        f"{len(working):,} working satellites, alongside inactive satellites, rocket bodies and debris. "
        "Explore them live on one globe, by owner, mission, constellation and orbit.")
    assert by_id(home, "get-started-button")["props"]["href"] == "/sat_visualisation"


def test_tiles_show_counts_from_the_data(callbacks, objects, working):
    home = page(callbacks, "/")
    assert f"{len(working):,}" in text(by_id(home, "tile-orbits"))
    constellations = working["satellite_constellation_name"].dropna().value_counts()
    tile = text(by_id(home, "tile-constellations"))
    assert tile.startswith(f"{len(constellations):,} ")
    top = constellations.sort_index().sort_values(ascending=False, kind="stable")
    assert top.index[0] in tile and f"{int(top.iloc[0]):,}" in tile
    systems = {s for v in working["satellite_system_names"] for s in (v or [])}
    assert text(by_id(home, "tile-systems")).startswith(f"{len(systems):,} ")
    missions = {m for v in working["mission_category_labels"] for m in (v or [])}
    assert text(by_id(home, "tile-missions")).startswith(f"{len(missions):,} ")
    junk = int(objects["object_type"].isin(["ROCKET BODY", "DEBRIS"]).sum())
    assert text(by_id(home, "tile-junk")).startswith(f"{junk:,} ")


def test_records_strip_counts_come_from_object_detail(callbacks, details):
    strip = " ".join(text(by_id(page(callbacks, "/"), "home-records")).split())   # one space between parts
    still = int(((details["flag_still_operating"] == 0) & (details["flag_still_transmitting"] == 1)).sum())
    several = int(details["owner_org_names"].map(lambda v: len(v or []) > 1).sum())
    assert f"{still:,} satellites have stopped operating but still transmit" in strip
    assert f"{several:,} objects have more than one owner on record" in strip
    assert f"{int((details['flag_mass_estimated'] == 1).sum()):,} masses are marked as estimates" in strip
    assert f"{int((details['flag_catalog_match_uncertain'] == 1).sum()):,} catalogue matches are marked as uncertain" in strip


@pytest.mark.parametrize("path", ["/", "/explore", "/sources", "/faq"] + [f"/explore/{k}" for k in VIEWS])
def test_every_link_leads_somewhere(callbacks, path):
    """No dead links: internal links go to a page the router knows (not the home page by default), the tracker (with
    or without a selection hash), or a publisher's site."""
    for href in links(page(callbacks, path)):
        if href.startswith("https://"):
            continue
        target = href.split("#")[0]
        assert target == "/" or page_for(target) != "home", href
        if target.startswith("/explore/"):
            assert target.split("/explore/")[1] in VIEWS, href
        if "#" in href:
            assert re.fullmatch(r"/sat_visualisation#v=1&sat=[1-9][0-9]*", href), href


@pytest.mark.parametrize("key", list(VIEWS))
def test_explore_view_ranks_working_satellites(callbacks, working, details, key):
    tree = page(callbacks, f"/explore/{key}")
    rows = [[text(td) for td in tr["props"]["children"]] for tr in walk(tree)
            if tr.get("type") == "Tr" and tr["props"]["children"][0].get("type") == "Td"]
    if key == "operators":
        ops = working.merge(details[["satcat_id", "operator_name"]], on="satcat_id", how="left")["operator_name"]
        counts = ops.dropna().value_counts()
    elif key in ("systems", "missions"):
        col = "satellite_system_names" if key == "systems" else "mission_category_labels"
        counts = working[col].explode().dropna().value_counts()
    else:
        col = {"constellations": "satellite_constellation_name", "countries": "owner_country", "orbits": "orbit_class"}[key]
        counts = working[col].dropna().value_counts()
    want = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:25]
    assert len(rows) == len(want) > 0
    assert [(r[1], r[2]) for r in rows] == [(name, f"{n:,}") for name, n in want]
    assert rows[0][3] == f"{100 * want[0][1] / len(working):.1f}%"
    assert [r[0] for r in rows] == [str(i + 1) for i in range(len(rows))]


def test_explore_summary_lists_every_view(callbacks):
    tree = page(callbacks, "/explore")
    for key, (title, _, _) in VIEWS.items():
        assert title in text(by_id(tree, f"explore-card-{key}"))
    assert set(links(tree)) >= {f"/explore/{k}" for k in VIEWS}


def test_faq_has_the_six_answers_from_the_apps_own_definitions(callbacks):
    tree = page(callbacks, "/faq")
    items = [n for n in walk(tree) if n.get("type") == "Details"]
    assert len(items) == 6
    whole = text(tree)
    for code, (name, _, rule) in ORBIT_HELP.items():          # the orbit answer is the filter panel's own wording
        assert f"{name} ({code}):" in whole and rule in whole
    assert "near-identical satellites working together" in whole          # D-047
    assert "believed to be still operating" in whole and "believed to be still transmitting" in whole   # GCAT's words
    assert "must not be used for conjunction (collision) assessment" in whole


def test_sources_credits_the_publishers_and_keeps_the_caution(callbacks):
    tree = page(callbacks, "/sources")
    whole = text(tree)
    for credit in ("USSPACECOM via Space-Track.org", "GCAT (J. McDowell, planet4589.org)", "CelesTrak (Dr T.S. Kelso)",
                   "CC BY 4.0"):
        assert credit in whole
    assert text(by_id(tree, "sources-caution")) == (
        "Public element sets must not be used for conjunction (collision) assessment.")


@pytest.mark.parametrize("path", ["/", "/explore", "/sources", "/faq"])
def test_no_claim_the_app_cannot_back(callbacks, path):
    whole = text(page(callbacks, path)).lower()
    for claim in ("open source", "open-source", "pass overhead", "15,000+"):
        assert claim not in whole

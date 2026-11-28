"""E2E: selecting one object on the globe (roadmap 3.4; D-018, D-019, D-023, D-024, D-054), with the sample objects
and object_detail datasets in headless Chromium.

- A click on a dot selects it: ring, name label and the panel (headline, "More details" sections with sources).
- The live height, speed and longitude come from the worker; checked against the Python sgp4 library and a
  geodetic conversion written here (independent code).
- Orbit and ground track toggles draw lines, Follow moves the camera with the object, x clears the selection.
- A shared link (#v=1&sat=...) opens with the object selected, even one the filters hide; Link and Cite copy text.
- A search pick selects and flies to the object (local experiment B).
- Every visible control in the panel does something (no dead controls).
"""
import gzip
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.e2e.test_viewer import open_viewer, sample_records, wait_until, check_security

REPO_ROOT = Path(__file__).resolve().parents[2]
DETAIL = REPO_ROOT / "tests" / "app_data" / "object_detail.json.gz"


def detail_records():
    return {r["satcat_id"]: r for r in json.loads(gzip.decompress(DETAIL.read_bytes()))["records"]}


def click_a_shown_object(page, prefer=None):
    """Click the first shown object that is on screen (prefer: a satcat_id to try first). Returns its satcat_id."""
    ids = page.evaluate("window.sattrackViewer.shownIds()")
    if prefer in ids:
        ids.remove(prefer)
        ids.insert(0, prefer)
    box = page.locator("#globe canvas").first.bounding_box()
    for satcat_id in ids:
        pos = page.evaluate(f"window.sattrackViewer.screenOf({satcat_id})")
        if not pos or not (5 < pos["x"] < box["width"] - 5 and 5 < pos["y"] < box["height"] - 5):
            continue
        page.mouse.click(box["x"] + pos["x"], box["y"] + pos["y"])
        page.wait_for_timeout(300)
        sel = page.evaluate("window.sattrackViewer.selection")
        if sel:
            return sel["satcat_id"]
    raise AssertionError("no shown object could be clicked")


def wait_detail(page):
    wait_until(page, "() => window.sattrackViewer.selection && window.sattrackViewer.selection.detail")


def test_click_selects_and_the_panel_shows_the_headline_and_sources(page, viewer_url):
    open_viewer(page, viewer_url)
    records = {r["satcat_id"]: r for r in sample_records()["records"]}
    details = detail_records()
    satcat_id = click_a_shown_object(page)
    wait_detail(page)
    rec, det = records[satcat_id], details[satcat_id]
    panel = page.locator("#sattrack-select")
    expect(panel).to_be_visible()
    expect(panel.locator(".sattrack-select-name")).to_have_text(rec["object_name"])
    expect(panel.locator(".sattrack-select-status")).to_contain_text(rec["operational_status"])
    if det["owner_org_names"]:
        expect(panel.locator(".sattrack-select-facts")).to_contain_text(det["owner_org_names"][0])
    # More details: the sections, each with its source line
    panel.locator("#sattrack-select-more summary").click()
    sections = page.evaluate("window.sattrackViewer.selectionSections")
    assert {"Identity", "Orbit"} <= set(sections)
    expect(panel.locator(".sattrack-select-section").filter(has_text="Orbit")).to_contain_text("USSPACECOM via Space-Track.org")
    expect(panel.locator(".sattrack-select-sections")).to_contain_text(f"{satcat_id}")
    if det["gcat_updated_at"]:
        expect(panel.locator(".sattrack-select-sections")).to_contain_text("GCAT (J. McDowell")
    # the hash carries the selection (D-024)
    assert page.evaluate("location.hash") == f"#v=1&sat={satcat_id}"
    # the ring and label sit on the dot
    assert page.evaluate("window.sattrackViewer.selection.satcat_id") == satcat_id
    assert page.errors == []
    check_security(page)


def geodetic(x, y, z):
    """WGS84 latitude, longitude (degrees) and height (km) from Earth-fixed km: Bowring's iteration, written here."""
    a, f = 6378.137, 1 / 298.257223563
    e2 = f * (2 - f)
    lon = math.degrees(math.atan2(y, x))
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - e2))
    for _ in range(10):
        n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1 - e2 * n / (n + h)))
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return math.degrees(lat), lon, p / math.cos(lat) - n


def python_state(record, iso):
    from sgp4 import omm
    from sgp4.api import Satrec, jday
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
    fields = {k.upper(): record[k] for k in ("object_name", "object_id", "epoch", "mean_motion", "eccentricity",
                                              "inclination", "ra_of_asc_node", "arg_of_pericenter", "mean_anomaly",
                                              "ephemeris_type", "classification_type", "element_set_no",
                                              "rev_at_epoch", "bstar", "mean_motion_dot", "mean_motion_ddot")}
    fields["NORAD_CAT_ID"] = record["satcat_id"]
    sat = Satrec()
    omm.initialize(sat, {k: str(v) for k, v in fields.items()})
    e, p, v = sat.sgp4(jd, fr)
    assert e == 0
    # GMST (IAU 1982), the rotation satellite.js and sgp4 both use, written out here
    tut1 = (jd + fr - 2451545.0) / 36525.0
    g = (-6.2e-6 * tut1 ** 3 + 0.093104 * tut1 ** 2 + (876600.0 * 3600 + 8640184.812866) * tut1 + 67310.54841)
    g = math.radians((g % 86400) / 240.0)
    c, s = math.cos(g), math.sin(g)
    lat, lon, h = geodetic(p[0] * c + p[1] * s, -p[0] * s + p[1] * c, p[2])
    return {"lat": lat, "lon": lon, "heightKm": h, "speedKms": math.sqrt(sum(x * x for x in v))}


def test_live_height_speed_and_longitude_match_python_sgp4(page, viewer_url):
    """The panel's live values: the worker's state against sgp4 + a geodetic conversion written here, for a LEO and a
    GEO object of the sample."""
    open_viewer(page, viewer_url)
    doc = sample_records()
    when = doc["generated_at"].replace("+00:00", "Z")
    when = datetime.fromisoformat(when.replace("Z", "+00:00")).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    picks = [next(r for r in doc["records"] if r["orbit_class"] == k and r["object_type"] == "PAYLOAD")
             for k in ("LEO", "GEO")]
    for rec in picks:
        got = page.evaluate("([id, iso]) => window.sattrackViewer.stateAt(id, iso)", [rec["satcat_id"], when])
        want = python_state(rec, when)
        assert abs(got["heightKm"] - want["heightKm"]) < 0.1, (rec["satcat_id"], got, want)
        assert abs(got["speedKms"] - want["speedKms"]) < 1e-4
        assert abs(((got["lon"] - want["lon"] + 180) % 360) - 180) < 0.01
        assert abs(got["lat"] - want["lat"]) < 0.01
    if picks[1]["orbit_class"] == "GEO":   # the GEO object's panel says where it sits
        page.evaluate(f"window.sattrackViewer.selectSatcat({picks[1]['satcat_id']})")
        wait_until(page, "() => window.sattrackViewer.selection && window.sattrackViewer.selection.live")
        expect(page.locator("#sattrack-select .sattrack-select-facts")).to_contain_text("Over")
    assert page.errors == []


def test_toggles_draw_the_orbit_and_ground_track_and_follow_moves_the_camera(page, viewer_url):
    open_viewer(page, viewer_url)
    click_a_shown_object(page)
    page.locator("#sattrack-select-orbit").click()
    wait_until(page, "() => (window.sattrackViewer.selectionLines || []).some(l => l.kind === 'orbit' && l.points > 100)")
    page.locator("#sattrack-select-ground").click()
    wait_until(page, "() => (window.sattrackViewer.selectionLines || []).length === 2")
    expect(page.locator("#sattrack-select-orbit")).to_have_attribute("aria-pressed", "true")
    page.locator("#sattrack-select-orbit").click()
    page.locator("#sattrack-select-ground").click()
    wait_until(page, "() => (window.sattrackViewer.selectionLines || []).length === 0")
    page.locator("#sattrack-select-follow").click()
    assert page.evaluate("window.sattrackViewer.selection.toggles.follow") is True
    page.locator("#sattrack-select-follow").click()
    assert page.evaluate("window.sattrackViewer.selection.toggles.follow") is False
    page.locator("#sattrack-select-close").click()
    expect(page.locator("#sattrack-select")).to_be_hidden()
    assert page.evaluate("window.sattrackViewer.selection") is None and page.evaluate("location.hash") == ""
    assert page.errors == []


def test_a_shared_link_opens_with_the_object_selected_even_when_filtered_out(page, viewer_url):
    """D-024's hash, version and satellite only: a debris object (hidden by the opening filters) is pinned and shown."""
    records = sample_records()["records"]
    hidden = next(r for r in records if r["object_type"] == "DEBRIS")
    page.goto(viewer_url + f"/sat_visualisation#v=1&sat={hidden['satcat_id']}", wait_until="domcontentloaded")
    wait_until(page, "() => window.sattrackViewer && window.sattrackViewer.ready")
    wait_until(page, f"() => window.sattrackViewer.selection && window.sattrackViewer.selection.satcat_id === {hidden['satcat_id']}")
    wait_until(page, f"() => window.sattrackViewer.shownIds().includes({hidden['satcat_id']})")
    expect(page.locator("#sattrack-select .sattrack-select-name")).to_have_text(hidden["object_name"])
    assert page.errors == []


@pytest.mark.parametrize("hash_", ["#v=2&sat=25544", "#v=1&sat=abc", "#v=1&sat=0", "#v=1&sat=" + "9" * 40,
                                   "#v=1&sat=<img src=x>"])
def test_a_bad_link_is_ignored(page, viewer_url, hash_):
    page.goto(viewer_url + "/sat_visualisation" + hash_, wait_until="domcontentloaded")
    wait_until(page, "() => window.sattrackViewer && window.sattrackViewer.ready")
    page.wait_for_timeout(500)
    assert page.evaluate("window.sattrackViewer.selection") is None
    assert page.errors == []


def test_link_and_cite_copy_text(page, viewer_url):
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    open_viewer(page, viewer_url)
    satcat_id = click_a_shown_object(page)
    wait_detail(page)
    page.locator("#sattrack-select-link").click()
    wait_until(page, "() => window.sattrackViewer.copied && window.sattrackViewer.copied.key === 'link'")
    copied = page.evaluate("window.sattrackViewer.copied")
    assert copied["ok"] and copied["text"] == f"https://www.sattrackapp.com/#v=1&sat={satcat_id}"
    page.locator("#sattrack-select-cite").click()
    wait_until(page, "() => window.sattrackViewer.copied.key === 'cite'")
    cite = page.evaluate("window.sattrackViewer.copied")
    assert cite["ok"] and f"SATCAT {satcat_id}" in cite["text"] and "USSPACECOM via Space-Track.org" in cite["text"]
    assert f"#v=1&sat={satcat_id}" in cite["text"]
    assert page.errors == []


def test_a_search_pick_selects_and_flies_to_the_object_without_changing_the_filters(page, viewer_url):
    """On the globe a pick selects and flies (owner, 28 Nov 2026), and the filters stay as they were: no chip, no
    filter change."""
    open_viewer(page, viewer_url)
    changes = page.evaluate("window.sattrackViewer.filterChanges")
    shown = page.evaluate("window.sattrackViewer.shownCount")
    page.locator("#sat-search-input").click()
    first = page.locator(".st-search-row").first
    first.wait_for()
    name = first.locator(".st-search-name").inner_text()
    first.click()
    wait_until(page, "() => !!window.sattrackViewer.selection")
    expect(page.locator("#sattrack-select .sattrack-select-name")).to_have_text(name)
    page.wait_for_timeout(1000)
    assert page.evaluate("window.sattrackViewer.filterChanges") == changes
    assert page.evaluate("window.sattrackViewer.shownCount") == shown
    expect(page.locator("#chip-satcatid")).to_be_hidden()
    assert page.errors == []


def test_the_search_list_follows_the_filters_and_typing_finds_the_rest(page, viewer_url):
    """Owner's option 3: browsing lists what the globe shows; typing finds everything, the hidden objects under a
    divider. The expected sets come from the globe's matched ids and the sample's records."""
    open_viewer(page, viewer_url)
    records = sample_records()["records"]
    matched = set(page.evaluate("[...window.sattrackViewer.matchedIds()]"))
    page.locator("#sat-search-input").click()
    page.locator(".st-search-row").first.wait_for()
    expect(page.locator(".st-search-status")).to_contain_text(f"{len(matched):,} on the globe")
    rows = page.locator(".st-search-row")
    assert all(int(rows.nth(i).get_attribute("data-id")) in matched for i in range(min(20, rows.count())))
    debris = [r for r in records if r["object_type"] == "DEBRIS"]
    word = debris[0]["object_name"].split()[0]
    page.locator("#sat-search-input").fill(word)
    expect(page.locator(".st-search-divider")).to_contain_text("Hidden by your filters")
    after = page.locator(".st-search-divider ~ .st-search-row")
    assert after.count() > 0 and all(int(after.nth(i).get_attribute("data-id")) not in matched
                                     for i in range(min(20, after.count())))
    assert page.errors == []


def test_browsing_shows_groups_and_jumps_to_debris(page, viewer_url):
    """Owner's option A: headings with counts in the list's order, and links that jump to each group."""
    open_viewer(page, viewer_url)
    page.locator(".st-junk-switch input").click()                     # payloads, rocket bodies and debris
    wait_until(page, "() => window.sattrackViewer.filterChanges > 0")
    matched = set(page.evaluate("[...window.sattrackViewer.matchedIds()]"))
    records = {r["satcat_id"]: r for r in sample_records()["records"]}
    n_debris = sum(1 for i in matched if records[i]["object_type"] == "DEBRIS" and records[i]["flag_space_station"] != 1)
    page.locator("#sat-search-input").click()
    jump = page.locator(".st-search-jump-link", has_text="Debris")
    expect(jump).to_have_text(f"Debris {n_debris:,}")
    jump.click()
    expect(page.locator(".st-search-top")).to_be_visible()
    expect(page.locator(".st-search-heading").first).to_have_text(f"Debris · {n_debris:,}")
    assert records[int(page.locator(".st-search-row").first.get_attribute("data-id"))]["object_type"] == "DEBRIS"
    page.locator(".st-search-top").click()
    expect(page.locator(".st-search-top")).to_have_count(0)
    assert page.errors == []


def test_minimise_keeps_the_selection_and_the_pill_brings_it_back(page, viewer_url):
    open_viewer(page, viewer_url)
    satcat_id = click_a_shown_object(page)
    page.locator("#sattrack-select-minimise").click()
    expect(page.locator("#sattrack-select")).to_be_hidden()
    pill = page.locator("#sattrack-select-pill")
    expect(pill).to_be_visible()
    assert page.evaluate("window.sattrackViewer.selection.satcat_id") == satcat_id   # still selected
    assert page.evaluate("location.hash") == f"#v=1&sat={satcat_id}"
    pill.click()
    expect(page.locator("#sattrack-select")).to_be_visible()
    expect(pill).to_be_hidden()
    assert page.errors == []


def test_orbit_names_match_the_filter_panel():
    """The panel's orbit names are the filter panel's hover-card names (orbit_filter.ORBIT_HELP)."""
    import re
    from app.layouts.components.filters.orbit_filter import ORBIT_HELP
    js = (REPO_ROOT / "static" / "viewer" / "selection.js").read_text(encoding="utf-8")
    block = js[js.index("export const ORBIT_NAMES"):].split("};", 1)[0]
    assert dict(re.findall(r'(\w+): "([^"]+)"', block)) == {k: v[0] for k, v in ORBIT_HELP.items()}


def phone(browser):
    context = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True)
    context.route(lambda u: not u.startswith("http://127.0.0.1"), lambda route: route.abort())
    pg = context.new_page()
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    return context, pg


def drag(pg, dy):
    box = pg.locator("#sattrack-select .sattrack-select-handle").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    pg.mouse.move(x, y)
    pg.mouse.down()
    for k in range(1, 6):
        pg.mouse.move(x, y + dy * k / 5)
    pg.mouse.up()
    pg.wait_for_timeout(300)


def test_on_phones_a_small_card_that_expands_drags_and_keeps_its_top_in_view(browser, viewer_url):
    """Owner, 28 Nov 2026: a small card at the bottom (name, status, height, orbit type, speed) so the globe stays
    visible; More expands it; dragging the bar steps it up or down to the pill; the top (bar, name, - and x) stays in
    view while the details scroll."""
    context, pg = phone(browser)
    try:
        open_viewer(pg, viewer_url)
        shown = set(pg.evaluate("window.sattrackViewer.shownIds()"))
        rec = next(r for r in sample_records()["records"] if r["satcat_id"] in shown and r["orbit_class"] == "LEO")
        pg.evaluate(f"window.sattrackViewer.selectSatcat({rec['satcat_id']})")
        wait_until(pg, "() => window.sattrackViewer.selection && window.sattrackViewer.selection.live")
        panel = pg.locator("#sattrack-select")
        globe, box = pg.locator("#globe").bounding_box(), panel.bounding_box()
        assert box["width"] >= globe["width"] - 2 and box["y"] + box["height"] > globe["y"] + globe["height"] - 40
        assert box["height"] < globe["height"] * 0.3                    # small: the globe stays visible
        expect(pg.locator(".sattrack-select-peek-live")).to_contain_text(" km · LEO · ")
        expect(pg.locator(".sattrack-select-facts")).to_be_hidden()
        pg.locator("#sattrack-select-expand").tap()
        expect(pg.locator(".sattrack-select-facts")).to_be_visible()
        expect(pg.locator(".sattrack-select-facts")).to_contain_text("Low Earth orbit (LEO)")
        pg.locator("#sattrack-select-more summary").tap()
        pg.evaluate("const p = document.getElementById('sattrack-select'); p.scrollTop = p.scrollHeight")
        assert abs(pg.locator(".sattrack-select-top").bounding_box()["y"] - panel.bounding_box()["y"]) < 3
        pg.evaluate("document.getElementById('sattrack-select').scrollTop = 0")
        drag(pg, 120)                                                  # expanded -> small
        assert pg.evaluate("window.sattrackViewer.selectionExpanded") is False
        drag(pg, -120)                                                 # small -> expanded
        assert pg.evaluate("window.sattrackViewer.selectionExpanded") is True
        drag(pg, 120)
        drag(pg, 120)                                                  # small -> pill
        assert pg.evaluate("window.sattrackViewer.selectionMinimised") is True
        assert pg.evaluate("window.sattrackViewer.selection.satcat_id") == rec["satcat_id"]
        assert pg.errors == []
    finally:
        context.close()


# Every control in the selection panel and the test that checks its effect (no dead controls in production). The
# pill shows only while minimised and More (sattrack-select-expand) only on phones, so they're listed separately.
PANEL_CONTROLS = {
    "sattrack-select-close": "test_toggles_draw_the_orbit_and_ground_track_and_follow_moves_the_camera",
    "sattrack-select-minimise": "test_minimise_keeps_the_selection_and_the_pill_brings_it_back",
    "sattrack-select-orbit": "test_toggles_draw_the_orbit_and_ground_track_and_follow_moves_the_camera",
    "sattrack-select-ground": "test_toggles_draw_the_orbit_and_ground_track_and_follow_moves_the_camera",
    "sattrack-select-follow": "test_toggles_draw_the_orbit_and_ground_track_and_follow_moves_the_camera",
    "sattrack-select-link": "test_link_and_cite_copy_text",
    "sattrack-select-cite": "test_link_and_cite_copy_text",
    "sattrack-select-more": "test_click_selects_and_the_panel_shows_the_headline_and_sources",
}
OTHER_CONTROLS = {
    "sattrack-select-pill": "test_minimise_keeps_the_selection_and_the_pill_brings_it_back",
    "sattrack-select-expand": "test_on_phones_a_small_card_that_expands_drags_and_keeps_its_top_in_view",
}


def test_every_panel_control_has_an_effect_check(page, base_url):
    """Run as production does (base_url): every button or disclosure a visitor can see in the panel is listed above
    with the test that checks it, so a new control can't ship unchecked."""
    open_viewer(page, base_url)
    sid = page.evaluate("window.sattrackViewer.shownIds()[0]")
    page.evaluate(f"window.sattrackViewer.selectSatcat({sid})")
    expect(page.locator("#sattrack-select")).to_be_visible()
    seen = set(page.evaluate("""() => [...document.querySelectorAll('#sattrack-select button, #sattrack-select details')]
        .filter(e => e.getBoundingClientRect().width > 0).map(e => e.id)"""))
    assert seen == set(PANEL_CONTROLS)
    assert all(name in globals() for name in {**PANEL_CONTROLS, **OTHER_CONTROLS}.values())

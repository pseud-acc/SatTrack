"""E2E guard: no filter control that does nothing reaches production (owner, 26 Nov 2026, after #82 shipped Space junk
mode to a production page that could only draw payloads).

Runs the app as production does (`base_url`: the Cesium viewer flag off) and checks two things:
  1. Coverage: every control a visitor can see in the filter panel (with its collapsed sections opened) has an
     effect check below. A new control without one fails here, so it can't ship unchecked.
  2. Effect: each control, used as a visitor would, changes what the visible view draws in the way the person
     asked for. "What they asked for" is worked out here with plain pandas over the sample's objects dataset (every
     object type), never with the app's code, so a control whose request the production views can't draw fails.

Each effect runs on a fresh page, so effects don't depend on each other.
"""
import gzip
import json
from datetime import datetime, timezone

import pandas as pd
import pytest
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeout

from _support import APP_DATA_DIR, load_sample, propagates
from test_journeys import PLOT_3D, choose_in_dropdown, open_tracker, trace_lengths, wait_for_traces

CHANGE_TIMEOUT = 20_000   # ms for the view to change after a control is used

# The visible controls: each element a visitor can operate (input, button, slider) mapped to its nearest Dash
# component id. The panel's own disclosure buttons (collapse, "Advanced Filters") open sections and filter nothing.
VISIBLE_CONTROLS = """() => {
  const ids = new Set();
  for (const e of document.querySelectorAll('#filter-collapse input, #filter-collapse button, #filter-collapse [role=slider]')) {
    if (e.classList.contains('accordion-button')) continue;
    const c = e.closest('[id]');
    if (!c || c.id === 'filter-collapse') continue;
    const r = c.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && !c.closest('[hidden]')) ids.add(c.id);
  }
  return [...ids].sort();
}"""


def open_sections(page):
    """Open every collapsed section of the panel, so the controls inside count as visible."""
    for button in page.locator("#filter-collapse .accordion-button.collapsed").all():
        button.click()
    page.evaluate("document.querySelectorAll('#filter-collapse details').forEach(d => d.open = true)")
    page.wait_for_timeout(500)


# ---- what the visitor asked for, from the objects dataset --------------------------------------------------------

def objects():
    doc = json.loads(gzip.decompress((APP_DATA_DIR / "objects.json.gz").read_bytes()))
    return pd.DataFrame.from_records(doc["records"])


def start_state():
    """The panel as production opens it: active payloads, every orbit class, the whole launch-year range."""
    return {"types": ["PAYLOAD"], "status": ["Active"], "orbit": ["LEO", "MEO", "GEO", "GSO", "HEO"],
            "name": None, "satcat": None, "owner": [], "vehicle": [], "purpose": [],
            "year": [1958, datetime.now(timezone.utc).year]}


def asked_for(df, s):
    """How many objects match state `s`. Inactive also covers a missing status; a missing year is outside any range."""
    st = df["operational_status"]
    keep = st.isin(s["status"]) | (st.isna() & ("Inactive" in s["status"]))
    keep &= df["object_type"].isin(s["types"]) & df["orbit_class"].isin(s["orbit"])
    keep &= df["launch_year"].between(*s["year"])
    if s["name"] is not None:
        keep &= df["object_name"] == s["name"]
    if s["satcat"] is not None:
        keep &= df["satcat_id"] == s["satcat"]
    if s["owner"]:
        keep &= df["owner_country"].isin(s["owner"])
    if s["vehicle"]:
        keep &= df["launch_vehicle_brand"].isin(s["vehicle"])
    if s["purpose"]:
        keep &= df["mission_category_labels"].map(lambda v: bool(set(v or []) & set(s["purpose"])))
    return int(keep.sum())


# ---- effects: (use the control, how the request changes) ----------------------------------------------------------

def most_common(column, df):
    return df[column].value_counts().index[0]


def _tick(box, label, on=True):
    def act(page):
        cb = page.locator(f"#{box}").get_by_label(label, exact=True)
        cb.check() if on else cb.uncheck()
    return act


def _pick(dropdown, label):
    return lambda page: choose_in_dropdown(page, dropdown, label)


def _drag_lower_year(page):
    """Drag the slider's lower thumb most of the way to the upper one, as a visitor would."""
    thumbs = page.locator("#launchyear-filter-slider [role=slider]")
    lo, hi = thumbs.first.bounding_box(), thumbs.nth(1).bounding_box()
    y = lo["y"] + lo["height"] / 2
    page.mouse.move(lo["x"] + lo["width"] / 2, y)
    page.mouse.down()
    page.mouse.move(hi["x"] - 30, y, steps=10)
    page.mouse.up()


def _slider_years(page):
    thumbs = page.locator("#launchyear-filter-slider [role=slider]")
    return [int(thumbs.nth(i).get_attribute("aria-valuenow")) for i in range(2)]


def effects():
    df, csv = objects(), load_sample()
    active_payloads = df[(df.object_type == "PAYLOAD") & (df.operational_status == "Active")]
    sat = csv[(csv.Status == "Active") & (csv.OrbitClass == "LEO")].iloc[0]
    owner = most_common("owner_country", active_payloads)
    vehicle = most_common("launch_vehicle_brand", active_payloads)
    return {
        "status-filter-checkbox": (_tick("status-filter-checkbox", "Inactive"),
                                   lambda s: {**s, "status": ["Active", "Inactive"]}),
        "orbit-filter-checkbox": (_tick("orbit-filter-checkbox", "LEO", on=False),
                                  lambda s: {**s, "orbit": [o for o in s["orbit"] if o != "LEO"]}),
        "satname-filter-dropdown": (_pick("satname-filter-dropdown", sat.ObjectName),
                                    lambda s: {**s, "name": sat.ObjectName}),
        "satcatid-filter-dropdown": (_pick("satcatid-filter-dropdown", str(sat.SatCatId)),
                                     lambda s: {**s, "satcat": int(sat.SatCatId)}),
        "owner-filter-multi-dropdown": (_pick("owner-filter-multi-dropdown", owner),
                                        lambda s: {**s, "owner": [owner]}),
        "launchvehicle-filter-multi-dropdown": (_pick("launchvehicle-filter-multi-dropdown", vehicle),
                                                lambda s: {**s, "vehicle": [vehicle]}),
        "purpose-filter-multi-dropdown": (_pick("purpose-filter-multi-dropdown", "Navigation"),
                                          lambda s: {**s, "purpose": ["Navigation"]}),
        # the lower thumb dragged up: the request is the range the slider then shows
        "launchyear-filter-slider": (_drag_lower_year, lambda s, page: {**s, "year": _slider_years(page)}),
        # Only the globe can draw them; listed so that offering them in production fails this test. Debris is all
        # Inactive in the sample, so the check starts from status Active + Inactive.
        "type-filter-checkbox": (lambda page: page.locator("#type-filter-checkbox").get_by_text("Debris", exact=True).click(),
                                 lambda s: {**s, "types": s["types"] + ["DEBRIS"]},
                                 _tick("status-filter-checkbox", "Inactive"),
                                 lambda s: {**s, "status": ["Active", "Inactive"]}),
        "junk-mode-switch": (lambda page: page.get_by_label("Space junk mode").check(),
                             lambda s: {**s, "types": ["PAYLOAD", "ROCKET BODY", "DEBRIS"],
                                        "status": ["Active", "Inactive"]}),
    }


# Buttons whose effect isn't a different set of objects: checked on their own below.
OWN_CHECKS = {"time-update-btn", "clear-orbits-btn"}


def test_every_visible_control_has_an_effect_check(page, base_url):
    open_tracker(page, base_url)
    open_sections(page)
    visible = set(page.evaluate(VISIBLE_CONTROLS))
    assert visible, "found no controls: the selector is out of date"
    unchecked = visible - set(effects()) - OWN_CHECKS
    assert not unchecked, f"controls offered in production with no effect check: {sorted(unchecked)}"


def wait_for_redraw(page, drawn):
    try:
        page.wait_for_function(
            """([id, n]) => (document.getElementById(id)?.querySelector('.js-plotly-plot')?.data?.[1]?.x || []).length !== n""",
            arg=[PLOT_3D, drawn], timeout=CHANGE_TIMEOUT)
    except PlaywrightTimeout:
        pass   # reported by the caller's assertion
    return trace_lengths(page, PLOT_3D)[1]


@pytest.mark.parametrize("control", list(effects()))
def test_each_visible_control_changes_the_view_as_asked(page, base_url, t_ref, control):
    """The view's change must match the request's, within the few sample objects SGP4 can't place: a control whose
    request the view can only partly draw (e.g. junk mode adding Inactive payloads but no debris) fails too."""
    open_tracker(page, base_url)
    open_sections(page)
    if control not in page.evaluate(VISIBLE_CONTROLS):
        return   # not offered in production: nothing to check (the coverage test above covers the reverse)
    act, change, *prep = effects()[control]
    df = objects()
    before_state = start_state()
    if prep:
        drawn = trace_lengths(page, PLOT_3D)[1]
        prep[0](page)
        wait_for_redraw(page, drawn)
        before_state = prep[1](before_state)
    unplaceable = int((~propagates(load_sample(), t_ref)).sum())
    drawn = trace_lengths(page, PLOT_3D)[1]
    act(page)
    after_state = change(before_state, page) if change.__code__.co_argcount == 2 else change(before_state)
    wanted = asked_for(df, after_state) - asked_for(df, before_state)
    assert wanted != 0, f"{control}: the chosen action asks for no change; pick another"
    now = wait_for_redraw(page, drawn)
    assert now != drawn and abs((now - drawn) - wanted) <= unplaceable, (
        f"{control} doesn't do what it offers in production: it asks for {wanted:+d} objects, the 3D view drew "
        f"{drawn} before and {now} after ({unplaceable} sample objects can't be placed)")
    assert page.errors == []


def test_update_button_redraws_the_views(page, base_url):
    """Update re-runs the views at the current time: clicking it makes the list callback answer with rows."""
    open_tracker(page, base_url)
    page.get_by_role("tab", name="List View").click()
    expect(page.locator("#satellite-list tbody tr:has(td)").first).to_be_visible()
    with page.expect_response(lambda r: "_dash-update-component" in r.url and r.status == 200) as resp:
        page.locator("#time-update-btn").click()
    assert "satellite-list" in resp.value.text()
    assert page.errors == []


def test_clear_orbits_removes_drawn_orbits(page, base_url):
    """A satellite clicked in the 3D view gets its orbit drawn; Clear Orbits removes it."""
    open_tracker(page, base_url)
    page.evaluate("""id => {
        const gd = document.getElementById(id).querySelector('.js-plotly-plot');
        gd.emit('plotly_click', {points: [{curveNumber: 1, pointNumber: 0, x: 0, y: 0, z: 0}]});
    }""", PLOT_3D)
    wait_for_traces(page, PLOT_3D, "lengths.length > 2")
    page.locator("#clear-orbits-btn").click()
    wait_for_traces(page, PLOT_3D, "lengths.length === 2")
    assert page.errors == []

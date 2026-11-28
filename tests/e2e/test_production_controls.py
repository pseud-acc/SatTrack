"""E2E guard: no filter control that does nothing reaches production (owner, 26 Nov 2026, after #82 shipped Space junk
mode to a production page that could only draw payloads).

Runs the app as production does (`base_url`: the globe on, the default since D-052) and checks two things:
  1. Coverage: every control a visitor can see in the filter panel (with its collapsed sections opened) has an
     effect check below. A new control without one fails here, so it can't ship unchecked.
  2. Effect: each control, used as a visitor would, changes what the visible view draws in the way the person
     asked for, on the globe. "What they asked for" is worked out here with plain pandas over the sample's objects
     dataset (every object type), never with the app's code, so a control whose request the globe can't draw fails.

Each effect runs on a fresh page, so effects don't depend on each other.
"""
import gzip
import json
from datetime import datetime, timezone

import pandas as pd
import pytest
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeout

from _support import APP_DATA_DIR
from test_journeys import choose_in_dropdown, open_tracker

CHANGE_TIMEOUT = 20_000   # ms for the view to change after a control is used

# The visible controls: each element a visitor can operate (input, button, slider) mapped to its nearest Dash
# component id. The panel's own disclosures (collapse, "More filters" rows) open sections and filter nothing.
VISIBLE_CONTROLS = """() => {
  const ids = new Set();
  for (const e of document.querySelectorAll('#filter-collapse input, #filter-collapse button, #filter-collapse [role=slider]')) {
    if (e.classList.contains('accordion-button')) continue;
    const c = e.closest('[id]');
    if (!c || c.id === 'filter-collapse' || c.tagName === 'DETAILS') continue;   // a section, not a control
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
            "constellation": [], "system": [], "primary": False,
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
    if s["constellation"]:
        keep &= df["satellite_constellation_name"].isin(s["constellation"])
    if s["system"]:   # every system the object is part of, or only the one it was built for (roadmap 3.14)
        keep &= (df["primary_satellite_system_name"].isin(s["system"]) if s["primary"]
                 else df["satellite_system_names"].map(lambda v: bool(set(v or []) & set(s["system"]))))
    return int(keep.sum())


def hosted_system(df):
    """A system some of `df`'s objects are part of without being built for it, so "built for" narrows it."""
    for r in df.itertuples():
        for s in (r.satellite_system_names or []):
            if s != r.primary_satellite_system_name:
                return s
    raise AssertionError("the sample has no hosted system among the active payloads")


# ---- effects: (use the control, how the request changes) ----------------------------------------------------------

def most_common(column, df):
    return df[column].value_counts().index[0]


def _segment(box, label):
    """Click one segment of a segmented control (roadmap 3.3b), as a visitor does: its input is visually hidden."""
    return lambda page: page.locator(f"#{box}").get_by_text(label, exact=True).click()


def _pick(dropdown, label):
    return lambda page: choose_in_dropdown(page, dropdown, label)


def _drag_lower_year(page):
    """Drag the slider's lower thumb most of the way to the upper one, as a visitor would."""
    thumbs = page.locator("#launchyear-filter-slider [role=slider]")
    thumbs.first.scroll_into_view_if_needed()   # the panel can be taller than the window (the search list, D-052)
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
    df = objects()
    active_payloads = df[(df.object_type == "PAYLOAD") & (df.operational_status == "Active")]
    sat = active_payloads[active_payloads.orbit_class == "LEO"].iloc[0]
    owner = most_common("owner_country", active_payloads)
    vehicle = most_common("launch_vehicle_brand", active_payloads)
    constellation = most_common("satellite_constellation_name", active_payloads)
    system = hosted_system(active_payloads)
    return {
        # Constellations and satellite systems (roadmap 3.14). The switch narrows a picked system to the objects built
        # for it, so its check picks a system first.
        "constellation-filter-multi-dropdown": (_pick("constellation-filter-multi-dropdown", constellation),
                                                lambda s: {**s, "constellation": [constellation]}),
        "system-filter-multi-dropdown": (_pick("system-filter-multi-dropdown", system),
                                         lambda s: {**s, "system": [system]}),
        "system-primary-switch": (lambda page: page.get_by_label("Only satellites built for the system").check(),
                                  lambda s: {**s, "primary": True},
                                  _pick("system-filter-multi-dropdown", system),
                                  lambda s: {**s, "system": [system]}),
        "status-filter-checkbox": (_segment("status-filter-checkbox", "All"),
                                   lambda s: {**s, "status": ["Active", "Inactive"]}),
        "orbit-filter-checkbox": (_segment("orbit-filter-checkbox", "LEO"),
                                  lambda s: {**s, "orbit": [o for o in s["orbit"] if o != "LEO"]}),
        "owner-filter-multi-dropdown": (_pick("owner-filter-multi-dropdown", owner),
                                        lambda s: {**s, "owner": [owner]}),
        "launchvehicle-filter-multi-dropdown": (_pick("launchvehicle-filter-multi-dropdown", vehicle),
                                                lambda s: {**s, "vehicle": [vehicle]}),
        "purpose-filter-multi-dropdown": (_pick("purpose-filter-multi-dropdown", "Navigation"),
                                          lambda s: {**s, "purpose": ["Navigation"]}),
        # the lower thumb dragged up: the request is the range the slider then shows
        "launchyear-filter-slider": (_drag_lower_year, lambda s, page: {**s, "year": _slider_years(page)}),
        # The globe draws every type (D-052). Debris is all Inactive in the sample, so the check starts from status
        # Active + Inactive.
        "type-filter-checkbox": (lambda page: page.locator("#type-filter-checkbox").get_by_text("Debris", exact=True).click(),
                                 lambda s: {**s, "types": s["types"] + ["DEBRIS"]},
                                 _segment("status-filter-checkbox", "All"),
                                 lambda s: {**s, "status": ["Active", "Inactive"]}),
        "junk-mode-switch": (lambda page: page.get_by_label("Space junk mode").check(),
                             lambda s: {**s, "types": ["PAYLOAD", "ROCKET BODY", "DEBRIS"],
                                        "status": ["Active", "Inactive"]}),
    }


# Roadmap 3.3b: each chip's remove button undoes its control, and Clear all undoes everything. Their checks are built
# from the control's own: use the control (so the chip shows), then remove it; the request goes back to the start.
CHIP_CONTROLS = {"status": "status-filter-checkbox", "orbit": "orbit-filter-checkbox",
                 "constellation": "constellation-filter-multi-dropdown", "system": "system-filter-multi-dropdown",
                 "owner": "owner-filter-multi-dropdown", "launchvehicle": "launchvehicle-filter-multi-dropdown",
                 "purpose": "purpose-filter-multi-dropdown", "year": "launchyear-filter-slider"}


def all_effects():
    base = effects()
    out = dict(base)
    # The status chip shows from the start ("Active"): removing it widens status to All.
    out["chip-x-status"] = (lambda page: page.locator("#chip-x-status").click(),
                            lambda s: {**s, "status": ["Active", "Inactive"]})
    for chip, control in CHIP_CONTROLS.items():
        if chip == "status":
            continue
        act, change = base[control][:2]
        out[f"chip-x-{chip}"] = (lambda page, c=chip: page.locator(f"#chip-x-{c}").click(),
                                 lambda s, page=None: start_state(), act, change)
    act, change = base["orbit-filter-checkbox"][:2]
    out["filter-clear-all"] = (lambda page: page.locator("#filter-clear-all").click(),
                               lambda s, page=None: start_state(), act, change)
    return out


# Controls whose effect isn't a different set of objects, checked elsewhere: the search box narrows the search list and
# its toggle opens and closes it (tests/e2e/test_journeys.py test_search_list_browses_narrows_and_picks); on the globe a
# pick from the list selects the object and flies to it without changing the filters, and its group links jump
# through the list (roadmap 3.4; tests/e2e/test_selection.py). Off the globe a pick filters, checked by the journeys.
OWN_CHECKS = {"sat-search-input", "sat-search-toggle", "sat-search-list", "sat-search"}


def test_every_visible_control_has_an_effect_check(page, base_url):
    open_tracker(page, base_url)
    open_sections(page)
    visible = set(page.evaluate(VISIBLE_CONTROLS))
    assert visible, "found no controls: the selector is out of date"
    unchecked = visible - set(all_effects()) - OWN_CHECKS
    assert not unchecked, f"controls offered in production with no effect check: {sorted(unchecked)}"


def shown(page):
    """Objects the globe shows now, plus those in its filter it can't place (SGP4 fails): what the filter selects."""
    return page.evaluate("window.sattrackViewer.shownCount + window.sattrackViewer.hiddenFailed")


def wait_for_redraw(page, changes):
    """Wait until the globe has applied one more filter change than `changes`, then return what it shows."""
    try:
        page.wait_for_function("n => window.sattrackViewer.filterChanges > n", arg=changes, timeout=CHANGE_TIMEOUT)
    except PlaywrightTimeout:
        pass   # reported by the caller's assertion
    return shown(page)


@pytest.mark.parametrize("control", list(all_effects()))
def test_each_visible_control_changes_the_view_as_asked(page, base_url, t_ref, control):
    """The globe's change must match the request's exactly: shown objects plus those in the filter it can't place,
    so a control whose request the globe can only partly draw fails too."""
    open_tracker(page, base_url)
    open_sections(page)
    act, change, *prep = all_effects()[control]
    df = objects()
    before_state = start_state()
    if prep:
        changes = page.evaluate("window.sattrackViewer.filterChanges")
        prep[0](page)
        wait_for_redraw(page, changes)
        before_state = (prep[1](before_state, page) if prep[1].__code__.co_argcount == 2 else prep[1](before_state))
    if control not in page.evaluate(VISIBLE_CONTROLS):
        return   # not offered in production: nothing to check (the coverage test above covers the reverse)
    drawn, changes = shown(page), page.evaluate("window.sattrackViewer.filterChanges")
    assert drawn == asked_for(df, before_state), f"{control}: the globe shows {drawn} before, expected {asked_for(df, before_state)}"
    act(page)
    after_state = change(before_state, page) if change.__code__.co_argcount == 2 else change(before_state)
    wanted = asked_for(df, after_state) - asked_for(df, before_state)
    assert wanted != 0, f"{control}: the chosen action asks for no change; pick another"
    now = wait_for_redraw(page, changes)
    assert now - drawn == wanted, (
        f"{control} doesn't do what it offers in production: it asks for {wanted:+d} objects, the globe showed "
        f"{drawn} before and {now} after")
    assert page.errors == []


def test_no_update_button(page, base_url):
    """Roadmap 3.3b: filters apply at once, so there's no Update button to press (or to do nothing)."""
    open_tracker(page, base_url)
    assert page.locator("#time-update-btn").count() == 0

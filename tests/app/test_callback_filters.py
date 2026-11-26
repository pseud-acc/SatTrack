"""Callback tests: the filter panel (app/callbacks/callback_filters.py), through /_dash-update-component, starting
from the page's own panel values.

Scope: the filter-spec store and Space junk mode (3.3a); the live count, the type switches' "matching / total", the
zero-match hints, the chips, Clear all and the "More filters" rows (3.3b), with counts from plain pandas over the
sample's objects dataset; the search lists are set once in the layout (Q8 S2); the collapse and fold buttons.
"""
import pytest

from _support import ALL_ORBITS, expected_object_count, objects_sample

SEARCH_NAME, SEARCH_ID = "satname-filter-dropdown", "satcatid-filter-dropdown"


@pytest.fixture(scope="module")
def objects():
    return objects_sample()


def test_search_lists_are_set_once_in_the_layout(callbacks, dependencies, sample_df):
    """Q8 S2: no callback rebuilds the search options (each rebuild re-indexed ~16k options); the layout has them all."""
    outputs = {o for d in dependencies for o in d["output"].strip(".").split("...")}
    assert not {o for o in outputs if o.endswith(".options") and o.split(".")[0] in (SEARCH_NAME, SEARCH_ID)}
    assert callbacks.initial(SEARCH_NAME, "options") == sorted(sample_df.ObjectName.unique())
    assert sorted(callbacks.initial(SEARCH_ID, "options"), key=int) == [str(i) for i in sorted(sample_df.SatCatId)]


def test_panel_strip_button(callbacks):
    """Desktop: the fold button adds st-panel-folded to the tracker row and takes it off again, keeping the
    row's other classes; the chevron points the way the panel will move."""
    def press(row_class):
        return callbacks.call("tracker-row", "panel-strip-toggle.n_clicks",
                              **{"panel-strip-toggle.n_clicks": 1, "tracker-row.className": row_class})
    base = "g-2 g-md-3 st-tracker-row"
    assert press(base) == (200, {"tracker-row.className": base + " st-panel-folded",
                                 "panel-strip-icon.className": "st-icon st-icon-chevron-right"})
    assert press(base + " st-panel-folded") == (200, {"tracker-row.className": base,
                                                      "panel-strip-icon.className": "st-icon st-icon-chevron-left"})


def test_collapse_button(callbacks):
    def press(n, is_open):
        return callbacks.call("filter-collapse", "toggle-filters.n_clicks",
                              **{"toggle-filters.n_clicks": n, "filter-collapse.is_open": is_open})
    assert press(1, False) == (200, {"filter-collapse.is_open": True, "toggle-icon.className": "st-icon st-icon-chevron-up"})
    assert press(2, True) == (200, {"filter-collapse.is_open": False, "toggle-icon.className": "st-icon st-icon-chevron-down"})
    assert press(None, False) == (200, {"filter-collapse.is_open": False,
                                        "toggle-icon.className": "st-icon st-icon-chevron-down"})


# ---- The filter-spec store and Space junk mode (roadmap 3.3a) ----------------------------------------------------

SPEC = "filter-spec"
CONTROLS_OUT = "junk-mode-switch"   # panel_controls: junk mode, chip removal, Clear all
TYPES, JUNK, STATUS, BEFORE = ("type-filter-checkbox.value", "junk-mode-switch.value", "status-filter-checkbox.value",
                               "status-before-junk.data")
ALL_ORBIT_CLASSES = ALL_ORBITS


def year_range(callbacks):
    return [int(y) for y in callbacks.initial("launchyear-filter-slider", "value")]


def test_filter_spec_starts_with_every_active_payload(callbacks):
    """The page opens on every active payload in any orbit class (owner, 26 Nov 2026), rendered into the store."""
    lo, hi = year_range(callbacks)
    assert callbacks.initial(SPEC, "data") == {"version": 1, "clauses": [
        {"field": "object_type", "op": "in", "value": ["PAYLOAD"]},
        {"field": "operational_status", "op": "in", "value": ["Active"]},
        {"field": "orbit_class", "op": "in", "value": ALL_ORBIT_CLASSES},
        {"field": "launch_year", "op": "between", "value": {"min": lo, "max": hi}},
    ]}


def test_filter_spec_follows_the_controls(callbacks):
    status, out = callbacks.call(SPEC, TYPES, **{TYPES: ["DEBRIS", "PAYLOAD"], STATUS: "All",
                                                 "orbit-filter-checkbox.value": ["LEO"],
                                                 "owner-filter-multi-dropdown.value": ["France", "Unknown"]})
    assert status == 200
    lo, hi = year_range(callbacks)
    assert out[f"{SPEC}.data"] == {"version": 1, "clauses": [
        {"field": "object_type", "op": "in", "value": ["PAYLOAD", "DEBRIS"]},          # display order
        {"field": "operational_status", "op": "in", "value": ["Active", "Inactive", None]},
        {"field": "orbit_class", "op": "in", "value": ["LEO"]},
        {"field": "launch_year", "op": "between", "value": {"min": lo, "max": hi}},
        {"field": "owner_country", "op": "in", "value": ["France", None]},             # "Unknown" is null (D-032)
    ]}


def test_no_type_ticked_selects_nothing(callbacks):
    status, out = callbacks.call(SPEC, TYPES, **{TYPES: []})
    assert status == 200 and out[f"{SPEC}.data"] is None


def test_junk_mode_on_adds_the_junk_types_and_inactive_then_off_restores(callbacks):
    status, on = callbacks.call(CONTROLS_OUT, JUNK, **{JUNK: True, TYPES: ["PAYLOAD"], STATUS: "Active"})
    assert status == 200
    assert on[TYPES] == ["PAYLOAD", "ROCKET BODY", "DEBRIS"]
    assert on[STATUS] == "All"                            # almost all rocket bodies and debris are Inactive
    assert on[BEFORE] == "Active"
    assert JUNK not in on                                 # the switch keeps the value the user gave it

    status, off = callbacks.call(CONTROLS_OUT, JUNK, **{JUNK: False, TYPES: on[TYPES], STATUS: on[STATUS],
                                                             BEFORE: on[BEFORE]})
    assert status == 200
    assert off[TYPES] == ["PAYLOAD"] and off[STATUS] == "Active" and off[BEFORE] is None


def test_ticking_both_junk_types_turns_the_switch_on_without_touching_status(callbacks):
    status, out = callbacks.call(CONTROLS_OUT, TYPES,
                                 **{JUNK: False, TYPES: ["PAYLOAD", "ROCKET BODY", "DEBRIS"], STATUS: "Active"})
    assert status == 200
    assert out[JUNK] is True and STATUS not in out and TYPES not in out


def test_unticking_one_junk_type_turns_the_switch_off(callbacks):
    status, out = callbacks.call(CONTROLS_OUT, TYPES,
                                 **{JUNK: True, TYPES: ["PAYLOAD", "DEBRIS"], STATUS: "All", BEFORE: "Active"})
    assert status == 200
    assert out[JUNK] is False and out[BEFORE] is None and STATUS not in out


def test_a_type_change_that_keeps_the_switch_state_changes_nothing(callbacks):
    status, _ = callbacks.call(CONTROLS_OUT, TYPES, **{JUNK: False, TYPES: ["DEBRIS"]})
    assert status == 204


# ---- What the panel shows (roadmap 3.3b) ---------------------------------------------------------------------------

SUMMARY = "filter-count"   # update_panel_summary's first output
CHIP_NAMES = ["types", "status", "orbit", "satname", "satcatid", "owner", "launchvehicle", "purpose", "year"]


def text(children):
    """Visible text of rendered Dash children (dicts from the JSON response, strings or lists)."""
    if children is None:
        return ""
    if isinstance(children, (str, int, float)):
        return str(children)
    if isinstance(children, list):
        return "".join(text(c) for c in children)
    if isinstance(children, dict):
        return text(children.get("props", {}).get("children"))
    return text(getattr(children, "children", None))   # a component from the layout


def summary(callbacks, **values):
    changed = next(iter(values), STATUS)
    status, out = callbacks.call(SUMMARY, changed, **values)
    assert status == 200
    return out


def type_cells(out):
    """object type -> (matching, total) from the type switches' options."""
    cells = {}
    for opt in out["type-filter-checkbox.options"]:
        m, total = text(opt["label"]["props"]["children"][2]).split(" / ")
        cells[opt["value"]] = (int(m.replace(",", "")), int(total.replace(",", "")))
    return cells


def shown_chips(out):
    return {n: out[f"chip-{n}-text.children"] for n in CHIP_NAMES if not out[f"chip-{n}.hidden"]}


def test_page_opens_with_the_count_of_active_payloads(callbacks, objects):
    """Rendered into the page (no callback at load). These tests run the app as production does (globe off), where the
    total is the payloads; with the globe on it is every object (tests/e2e/test_viewer.py)."""
    n = expected_object_count(objects)
    payloads = int((objects["object_type"] == "PAYLOAD").sum())   # production: the globe is off, so payloads (#83)
    assert text(callbacks.initial(SUMMARY, "children")) == f"{n:,}of {payloads:,} payloads"
    assert n > 0


@pytest.mark.parametrize("values, expect", [
    ({STATUS: "All"}, dict(status="All")),
    ({STATUS: "Inactive", TYPES: ["DEBRIS", "ROCKET BODY"]}, dict(status="Inactive", types=["DEBRIS", "ROCKET BODY"])),
    ({"orbit-filter-checkbox.value": ["LEO"], STATUS: "All", TYPES: ["PAYLOAD", "DEBRIS"]},
     dict(status="All", orbit=["LEO"], types=["PAYLOAD", "DEBRIS"])),
    ({"launchyear-filter-slider.value": [2000, 2015]}, dict(year=[2000, 2015])),
    ({"orbit-filter-checkbox.value": []}, dict(orbit=[])),
    ({TYPES: []}, dict(types=[])),
], ids=["all-status", "junk-inactive", "leo", "years", "no-orbit", "no-type"])
def test_count_and_type_counts_follow_the_controls(callbacks, objects, values, expect):
    out = summary(callbacks, **values)
    n = expected_object_count(objects, **expect)
    payloads = int((objects["object_type"] == "PAYLOAD").sum())
    assert text(out[f"{SUMMARY}.children"]) == f"{n:,}of {payloads:,} payloads"
    others = {k: v for k, v in expect.items() if k != "types"}
    for t, (m, total) in type_cells(out).items():
        assert m == expected_object_count(objects, **{**others, "types": [t]}), t   # matching the other filters
        assert total == int((objects["object_type"] == t).sum()), t


def test_count_equals_the_store_spec_on_the_server(callbacks, app_module):
    """Q4: the count is the filter-spec store's spec, applied to the filter table."""
    from app.core import filter_spec
    from app.core.state import get_app_data
    values = {STATUS: "All", TYPES: ["PAYLOAD", "ROCKET BODY"], "orbit-filter-checkbox.value": ["LEO", "MEO"]}
    spec = callbacks.spec_for(values)
    table = get_app_data()["filter"]["table"]
    out = summary(callbacks, **values)
    assert text(out[f"{SUMMARY}.children"]).startswith(f"{int(filter_spec.apply(spec, table).sum()):,}of")


def test_a_shown_type_matching_nothing_says_why(callbacks, objects):
    assert expected_object_count(objects, status="Active", types=["DEBRIS"]) == 0     # the sample's debris: all Inactive
    out = summary(callbacks, **{TYPES: ["PAYLOAD", "DEBRIS"]})
    assert [text(h) for h in out["type-hint.children"]] == ["Debris: 0 match, because status is Active."]
    out = summary(callbacks, **{TYPES: ["DEBRIS"], STATUS: "All", "launchyear-filter-slider.value": [1958, 1958]})
    assert expected_object_count(objects, status="All", types=["DEBRIS"], year=[1958, 1958]) == 0
    assert [text(h) for h in out["type-hint.children"]] == ["Debris: 0 match the other filters."]
    assert summary(callbacks, **{STATUS: "All"})["type-hint.children"] == []


def test_chips_show_what_narrows_and_rows_show_their_values(callbacks):
    start = callbacks.initial
    assert {n: start(f"chip-{n}-text", "children") for n in CHIP_NAMES if not start(f"chip-{n}", "hidden")} == {
        "types": "Payloads", "status": "Active"}
    assert start("filter-clear-all", "hidden") is True          # nothing differs from the opening values
    out = summary(callbacks, **{
        STATUS: "All", TYPES: ["PAYLOAD", "DEBRIS"], "orbit-filter-checkbox.value": ["GEO", "LEO"],
        "owner-filter-multi-dropdown.value": ["France", "Japan", "Unknown"], "purpose-filter-multi-dropdown.value":
        ["Navigation"], "launchyear-filter-slider.value": [1990, 2005], f"{SEARCH_ID}.value": "25544"})
    assert shown_chips(out) == {
        "types": "Payloads, Debris", "orbit": "Orbit type: LEO, GEO", "satcatid": "SATCAT number: 25544",
        "owner": "Owner: France +2", "purpose": "Purpose: Navigation", "year": "Launch year: 1990–2005"}
    assert out["filter-clear-all.hidden"] is False
    assert [out[f"more-{r}-summary.children"] for r in ("owner", "launchvehicle", "purpose", "year")] == [
        "France +2", "Any", "Navigation", "1990–2005"]


@pytest.mark.parametrize("chip, control, widened", [
    ("status", STATUS, "All"),
    ("orbit", "orbit-filter-checkbox.value", ALL_ORBITS),
    ("owner", "owner-filter-multi-dropdown.value", []),
    ("satcatid", f"{SEARCH_ID}.value", None),
])
def test_a_chips_remove_button_widens_only_its_control(callbacks, chip, control, widened):
    status, out = callbacks.call(CONTROLS_OUT, f"chip-x-{chip}.n_clicks", **{f"chip-x-{chip}.n_clicks": 1})
    assert status == 200
    assert out == {control: widened}


def test_clear_all_restores_the_opening_values(callbacks):
    status, out = callbacks.call(CONTROLS_OUT, "filter-clear-all.n_clicks", **{
        "filter-clear-all.n_clicks": 1, JUNK: True, TYPES: ["DEBRIS"], STATUS: "Inactive", BEFORE: "Active"})
    assert status == 200
    lo, hi = year_range(callbacks)
    assert out == {JUNK: False, TYPES: ["PAYLOAD"], STATUS: "Active", BEFORE: None,
                   "orbit-filter-checkbox.value": ALL_ORBITS, f"{SEARCH_NAME}.value": None, f"{SEARCH_ID}.value": None,
                   "owner-filter-multi-dropdown.value": [], "launchvehicle-filter-multi-dropdown.value": [],
                   "purpose-filter-multi-dropdown.value": [], "launchyear-filter-slider.value": [lo, hi]}

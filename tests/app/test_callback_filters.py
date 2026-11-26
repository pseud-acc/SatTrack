"""Callback tests: the sidebar (app/callbacks/callback_filters.py), through /_dash-update-component, starting
from the page's own sidebar values.

Scope: the name and catalogue-number dropdowns offer exactly the satellites the other filters allow, keep a
selection that still matches and clear one that doesn't; the collapse button opens and closes the filters;
the launch-year labels show the slider's range.
"""
from _support import expected_ids

SEARCH = "satname-filter-dropdown"
NAME_OPTS, ID_OPTS = f"{SEARCH}.options", "satcatid-filter-dropdown.options"
NAME_VAL, ID_VAL = f"{SEARCH}.value", "satcatid-filter-dropdown.value"


def ids_as_options(ids):
    return [str(i) for i in sorted(ids)]


def test_search_options_follow_the_filters(callbacks, sample_df, t_ref):
    values = {"status-filter-checkbox.value": ["Inactive"]}
    status, out = callbacks.call(SEARCH, "status-filter-checkbox.value", **values)
    assert status == 200
    ids = expected_ids(sample_df, t_ref, **callbacks.filter_args(values))
    assert len(ids) > 0
    assert out[ID_OPTS] == ids_as_options(ids)
    assert out[NAME_OPTS] == sorted(set(sample_df[sample_df.SatCatId.isin(ids)].ObjectName))
    assert out[NAME_VAL] is None and out[ID_VAL] is None


def test_selection_kept_while_it_matches(callbacks, sample_df, t_ref):
    allowed = expected_ids(sample_df, t_ref, **callbacks.filter_args({}))
    sat = min(allowed)
    status, out = callbacks.call(SEARCH, ID_VAL, **{ID_VAL: str(sat)})
    assert status == 200
    assert out[ID_VAL] == str(sat) and out[ID_OPTS] == [str(sat)]


def test_selection_cleared_when_it_no_longer_matches(callbacks, sample_df, t_ref):
    sat = sample_df[sample_df.Status == "Inactive"].iloc[0].SatCatId
    values = {"status-filter-checkbox.value": ["Active"]}
    status, out = callbacks.call(SEARCH, "status-filter-checkbox.value", **{**values, ID_VAL: str(sat)})
    assert status == 200
    assert out[ID_VAL] is None and out[NAME_VAL] is None
    assert out[ID_OPTS] == ids_as_options(expected_ids(sample_df, t_ref, **callbacks.filter_args(values)))


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


def test_launch_year_labels(callbacks):
    status, out = callbacks.call("launch-year-min-display", "launchyear-filter-slider.value",
                                 **{"launchyear-filter-slider.value": [1990, 2005]})
    assert status == 200
    assert "1990" in str(out["launch-year-min-display.children"])
    assert "2005" in str(out["launch-year-max-display.children"])
    status, _ = callbacks.call("launch-year-min-display", "launchyear-filter-slider.value",
                               **{"launchyear-filter-slider.value": None})
    assert status == 204


# ---- The filter-spec store and Space junk mode (roadmap 3.3a) ----------------------------------------------------

SPEC = "filter-spec"
TYPES, JUNK, STATUS, BEFORE = ("type-filter-checkbox.value", "junk-mode-switch.value", "status-filter-checkbox.value",
                               "status-before-junk.data")
ALL_ORBIT_CLASSES = ["LEO", "MEO", "GEO", "GSO", "HEO"]


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
    status, out = callbacks.call(SPEC, TYPES, **{TYPES: ["DEBRIS", "PAYLOAD"], STATUS: ["Active", "Inactive"],
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
    status, on = callbacks.call("junk-mode-switch", JUNK, **{JUNK: True, TYPES: ["PAYLOAD"], STATUS: ["Active"]})
    assert status == 200
    assert on[TYPES] == ["PAYLOAD", "ROCKET BODY", "DEBRIS"]
    assert on[STATUS] == ["Active", "Inactive"]          # almost all rocket bodies and debris are Inactive
    assert on[BEFORE] == ["Active"]
    assert JUNK not in on                                 # the switch keeps the value the user gave it

    status, off = callbacks.call("junk-mode-switch", JUNK, **{JUNK: False, TYPES: on[TYPES], STATUS: on[STATUS],
                                                             BEFORE: on[BEFORE]})
    assert status == 200
    assert off[TYPES] == ["PAYLOAD"] and off[STATUS] == ["Active"] and off[BEFORE] is None


def test_ticking_both_junk_types_turns_the_switch_on_without_touching_status(callbacks):
    status, out = callbacks.call("junk-mode-switch", TYPES,
                                 **{JUNK: False, TYPES: ["PAYLOAD", "ROCKET BODY", "DEBRIS"], STATUS: ["Active"]})
    assert status == 200
    assert out[JUNK] is True and STATUS not in out and TYPES not in out


def test_unticking_one_junk_type_turns_the_switch_off(callbacks):
    status, out = callbacks.call("junk-mode-switch", TYPES,
                                 **{JUNK: True, TYPES: ["PAYLOAD", "DEBRIS"], STATUS: ["Active", "Inactive"],
                                    BEFORE: ["Active"]})
    assert status == 200
    assert out[JUNK] is False and out[BEFORE] is None and STATUS not in out


def test_a_type_change_that_keeps_the_switch_state_changes_nothing(callbacks):
    status, _ = callbacks.call("junk-mode-switch", TYPES, **{JUNK: False, TYPES: ["DEBRIS"]})
    assert status == 204

"""Callback tests: the sidebar (app/callbacks/callback_filters.py), through /_dash-update-component, starting
from the page's own sidebar values.

Scope: the name and catalogue-number dropdowns start empty and offer at most 50 matches for what is typed, among
the satellites the other filters allow (server-side search: Dash 4's Dropdown indexes every option in the browser);
they keep a selection that still matches, without re-sending it, and clear one that doesn't; the collapse button
opens and closes the filters; the launch-year labels show the slider's range.
"""
from _support import expected_ids

SEARCH = "satname-filter-dropdown"
NAME_OPTS, ID_OPTS = f"{SEARCH}.options", "satcatid-filter-dropdown.options"
NAME_VAL, ID_VAL = f"{SEARCH}.value", "satcatid-filter-dropdown.value"
NAME_SEARCH, ID_SEARCH = f"{SEARCH}.search_value", "satcatid-filter-dropdown.search_value"


def names_of(sample_df, ids):
    return sorted(set(sample_df[sample_df.SatCatId.isin(ids)].ObjectName))


def test_dropdowns_start_empty(callbacks):
    status, out = callbacks.call(SEARCH, "status-filter-checkbox.value")
    assert status == 200
    assert out[NAME_OPTS] == [] and out[ID_OPTS] == []
    assert NAME_VAL not in out and ID_VAL not in out   # values untouched: typing never redraws the figures


def test_satcat_search_offers_numbers_starting_with_the_digits(callbacks, sample_df, t_ref):
    values = {"status-filter-checkbox.value": ["Inactive"]}
    ids = expected_ids(sample_df, t_ref, **callbacks.filter_args(values))
    digits = str(min(ids))[:2]
    status, out = callbacks.call(SEARCH, ID_SEARCH, **values, **{ID_SEARCH: digits})
    assert status == 200
    want = sorted(i for i in ids if str(i).startswith(digits))[:50]
    assert out[ID_OPTS] == [str(i) for i in want] and want


def test_name_search_puts_prefix_matches_first_and_caps_at_50(callbacks, sample_df, t_ref):
    ids = expected_ids(sample_df, t_ref, **callbacks.filter_args({}))
    names = names_of(sample_df, ids)
    text = "st"   # matches both at the start (STARLINK-...) and inside (e.g. COSMOS) in the sample
    status, out = callbacks.call(SEARCH, NAME_SEARCH, **{NAME_SEARCH: text.upper()})
    assert status == 200
    starts = [n for n in names if n.lower().startswith(text)]
    inside = [n for n in names if text in n.lower() and not n.lower().startswith(text)]
    assert out[NAME_OPTS] == (starts + inside)[:50]
    assert 0 < len(out[NAME_OPTS]) <= 50


def test_search_only_offers_satellites_the_filters_allow(callbacks, sample_df, t_ref):
    values = {"status-filter-checkbox.value": ["Active"]}
    inactive = sample_df[sample_df.Status == "Inactive"].iloc[0]
    status, out = callbacks.call(SEARCH, ID_SEARCH, **values, **{ID_SEARCH: str(inactive.SatCatId)})
    assert status == 200
    assert str(inactive.SatCatId) not in out[ID_OPTS]


def test_selection_kept_while_it_matches(callbacks, sample_df, t_ref):
    allowed = expected_ids(sample_df, t_ref, **callbacks.filter_args({}))
    sat = min(allowed)
    status, out = callbacks.call(SEARCH, ID_VAL, **{ID_VAL: str(sat)})
    assert status == 200
    assert ID_VAL not in out and NAME_VAL not in out   # kept: not re-sent
    assert out[ID_OPTS] == [str(sat)]   # still offered, so the dropdown can display it


def test_selection_cleared_when_it_no_longer_matches(callbacks, sample_df, t_ref):
    sat = sample_df[sample_df.Status == "Inactive"].iloc[0].SatCatId
    values = {"status-filter-checkbox.value": ["Active"]}
    status, out = callbacks.call(SEARCH, "status-filter-checkbox.value", **{**values, ID_VAL: str(sat)})
    assert status == 200
    assert out[ID_VAL] is None and out[NAME_VAL] is None
    assert out[ID_OPTS] == [] and out[NAME_OPTS] == []


def test_collapse_button(callbacks):
    def press(n, is_open):
        return callbacks.call("filter-collapse", "toggle-filters.n_clicks",
                              **{"toggle-filters.n_clicks": n, "filter-collapse.is_open": is_open})
    assert press(1, False) == (200, {"filter-collapse.is_open": True, "toggle-icon.className": "fas fa-chevron-up"})
    assert press(2, True) == (200, {"filter-collapse.is_open": False, "toggle-icon.className": "fas fa-chevron-down"})
    assert press(None, False) == (200, {"filter-collapse.is_open": False,
                                        "toggle-icon.className": "fas fa-chevron-down"})


def test_launch_year_labels(callbacks):
    status, out = callbacks.call("launch-year-min-display", "launchyear-filter-slider.value",
                                 **{"launchyear-filter-slider.value": [1990, 2005]})
    assert status == 200
    assert "1990" in str(out["launch-year-min-display.children"])
    assert "2005" in str(out["launch-year-max-display.children"])
    status, _ = callbacks.call("launch-year-min-display", "launchyear-filter-slider.value",
                               **{"launchyear-filter-slider.value": None})
    assert status == 204

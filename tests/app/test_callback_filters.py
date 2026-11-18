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

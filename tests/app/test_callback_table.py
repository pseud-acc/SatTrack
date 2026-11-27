"""Callback tests: the list view (update_tbl in app/callbacks/callback_table.py), through
/_dash-update-component, starting from the page's own sidebar values.

Scope: the table holds exactly the expected satellites, sorted by name, with the documented columns and the
time of the positions; it is built only while its tab is open, and opening the tab again with unchanged filters
sends nothing (D-052).
"""
import pytest

from _support import expected_ids
from app.helper.helper__table_display import create_table_mapping

OUT = "tab-list-body"
BODY, SHOWN = f"{OUT}.children", "list-shown-spec.data"
TAB = {"sat-viz-tabs.active_tab": "tbl-viz"}


def table_rows(out):
    """The DataTable's rows from the tab's contents (its first child, id satellite-list)."""
    table = out[BODY][0]
    assert table["props"]["id"] == "satellite-list"
    return table["props"]["data"]


@pytest.mark.parametrize("values", [{}, {"orbit-filter-checkbox.value": ["GSO"]}], ids=["start", "GSO"])
def test_table_rows_and_columns(callbacks, sample_df, t_ref, values):
    status, out = callbacks.call(OUT, "orbit-filter-checkbox.value", **{**TAB, **values})
    assert status == 200
    rows = table_rows(out)
    mapping = create_table_mapping()
    assert all(list(r) == list(mapping.values()) for r in rows)
    expected = expected_ids(sample_df, t_ref, **callbacks.filter_args(values))
    assert len(expected) > 0
    assert {r[mapping["SatCatId"]] for r in rows} == expected
    names = [r[mapping["ObjectName"]] for r in rows]
    assert names == sorted(names)
    assert {r[mapping["Datetime"]] for r in rows} == {t_ref.strftime("%H:%M:%S, %d/%m/%Y")}


@pytest.mark.parametrize("tab", ["globe", "2d-viz"])
def test_other_tabs_do_not_run_it(callbacks, tab):
    status, _ = callbacks.call(OUT, "orbit-filter-checkbox.value", **{"sat-viz-tabs.active_tab": tab})
    assert status == 204


def test_reopening_with_the_same_filters_sends_nothing(callbacks):
    """Owner, 27 Nov 2026: every tab switch rebuilt the list (~4 MB). The spec it was built for is kept; opening the
    tab again with that spec is a no-op, and a changed spec rebuilds it."""
    status, out = callbacks.call(OUT, "sat-viz-tabs.active_tab", **TAB)
    assert status == 200 and out[SHOWN]["spec"]
    status, _ = callbacks.call(OUT, "sat-viz-tabs.active_tab",
                               **{**TAB, SHOWN: out[SHOWN], "filter-spec.data": out[SHOWN]["spec"]})
    assert status == 204
    status, again = callbacks.call(OUT, "orbit-filter-checkbox.value",
                                   **{**TAB, SHOWN: out[SHOWN], "orbit-filter-checkbox.value": ["GSO"]})
    assert status == 200 and again[SHOWN] != out[SHOWN]

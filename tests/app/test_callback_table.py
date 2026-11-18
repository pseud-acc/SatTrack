"""Callback tests: the list view (update_tbl in app/callbacks/callback_table.py), through
/_dash-update-component, starting from the page's own sidebar values.

Scope: the table holds exactly the expected satellites, sorted by name, with the documented columns and the
time of the positions; other tabs don't run it.
"""
import pytest

from _support import expected_ids
from app.helper.helper__table_display import create_table_mapping

OUT = "satellite-list"
DATA = f"{OUT}.data"
TAB = {"sat-viz-tabs.active_tab": "tbl-viz"}


@pytest.mark.parametrize("values", [{}, {"orbit-filter-checkbox.value": ["GSO"]}], ids=["start", "GSO"])
def test_table_rows_and_columns(callbacks, sample_df, t_ref, values):
    status, out = callbacks.call(OUT, "orbit-filter-checkbox.value", **{**TAB, **values})
    assert status == 200
    rows = out[DATA]
    mapping = create_table_mapping()
    assert all(list(r) == list(mapping.values()) for r in rows)
    expected = expected_ids(sample_df, t_ref, **callbacks.filter_args(values))
    assert len(expected) > 0
    assert {r[mapping["SatCatId"]] for r in rows} == expected
    names = [r[mapping["ObjectName"]] for r in rows]
    assert names == sorted(names)
    assert {r[mapping["Datetime"]] for r in rows} == {t_ref.strftime("%H:%M:%S, %d/%m/%Y")}


@pytest.mark.parametrize("tab", ["3d-viz", "2d-viz"])
def test_other_tabs_do_not_run_it(callbacks, tab):
    status, _ = callbacks.call(OUT, "orbit-filter-checkbox.value", **{"sat-viz-tabs.active_tab": tab})
    assert status == 204

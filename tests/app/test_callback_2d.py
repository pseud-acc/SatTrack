"""Callback tests: the 2D map (update_2dviz in app/callbacks/callback_2d_viz.py), through
/_dash-update-component, starting from the page's own sidebar values.

Scope: with several satellites selected the map shows no track; with exactly one it shows that satellite's
ground track for one period (3,600 points) with its current position as the track's first point; other tabs
don't run it. Longitude range is covered in test_satellite_position.py.
"""
import pytest
from _support import STATUS_KEEPS

OUT = "2d-earth-satellite-plot"
FIG = f"{OUT}.figure"
TAB = {"sat-viz-tabs.active_tab": "2d-viz"}


def test_many_satellites_show_no_track(callbacks):
    status, out = callbacks.call(OUT, "status-filter-checkbox.value", **TAB)
    assert status == 200
    assert all(len(t.get("lat", [])) <= 1 for t in out[FIG]["data"])   # only the empty placeholder


def test_one_satellite_shows_its_ground_track(callbacks, sample_df):
    start = callbacks.filter_args({})
    sat = sample_df[sample_df.Status.isin(STATUS_KEEPS[start["status"]]) & (sample_df.OrbitClass == "LEO")].iloc[0]
    status, out = callbacks.call(OUT, "satcatid-filter-dropdown.value",
                                 **{**TAB, "satcatid-filter-dropdown.value": str(sat.SatCatId)})
    assert status == 200
    current, path = out[FIG]["data"]
    assert len(path["lat"]) == 3600
    assert current["lat"] == [path["lat"][0]] and current["lon"] == [path["lon"][0]]
    assert all(-90 <= lat <= 90 for lat in path["lat"])
    assert "Current Position" in current["hovertext"]


@pytest.mark.parametrize("tab", ["3d-viz", "tbl-viz"])
def test_other_tabs_do_not_run_it(callbacks, tab):
    status, _ = callbacks.call(OUT, "status-filter-checkbox.value", **{"sat-viz-tabs.active_tab": tab})
    assert status == 204

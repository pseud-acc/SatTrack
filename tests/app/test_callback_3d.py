"""Callback tests: the 3D view (update_3dviz in app/callbacks/callback_3d_viz.py), called through
/_dash-update-component as the browser calls it, starting from the page's own sidebar values.

Scope: a filter change draws the full figure with exactly the expected satellites; a timer tick with the same
satellites sends only a patch; a tick after the set changed redraws; clicking a satellite tracks its orbit,
clicking it again does nothing, Clear Orbits empties the list; other tabs don't run it.
"""
import pytest

from _support import expected_ids

OUT = "3d-earth-satellite-plot"
FIG, ORBITS, CAMERA, IDS = (f"{OUT}.figure", "3d-orbit-memory.data", "camera-memory.data", "3d-sat-ids.data")
TICK = "3d-viz-interval-component.n_intervals"
TAB = {"sat-viz-tabs.active_tab": "3d-viz"}


def draw(callbacks, changed="status-filter-checkbox.value", **values):
    status, out = callbacks.call(OUT, changed, **{**TAB, **values})
    return status, out


@pytest.mark.parametrize("values", [
    {},                                                           # the page as it opens
    {"status-filter-checkbox.value": "All", "orbit-filter-checkbox.value": ["MEO", "HEO"]},
], ids=["start", "changed-filters"])
def test_filter_change_draws_expected_satellites(callbacks, sample_df, t_ref, values):
    status, out = draw(callbacks, **values)
    assert status == 200
    fig = out[FIG]
    assert fig["data"][0]["type"] == "surface"                    # Earth
    assert fig["data"][1]["type"] == "scatter3d"
    expected = expected_ids(sample_df, t_ref, **callbacks.filter_args(values))
    assert len(expected) > 0
    assert len(fig["data"][1]["x"]) == len(expected)
    assert out[IDS].startswith(f"{len(expected)}:")
    assert out[ORBITS] == [] and len(fig["data"]) == 2           # no orbits tracked yet


def test_tick_with_same_satellites_sends_only_a_patch(callbacks):
    ids = draw(callbacks)[1][IDS]
    status, out = draw(callbacks, TICK, **{IDS: ids, TICK: 1})
    assert status == 200
    assert set(out) == {FIG}                                      # other outputs: no_update
    assert out[FIG].get("__dash_patch_update") == "__dash_patch_update"
    paths = {tuple(op["location"]) for op in out[FIG]["operations"]}
    assert ("data", 1, "x") in paths and ("data", 1, "text") in paths
    assert not any(p[:2] == ("data", 0) for p in paths)           # the Earth surface is not resent


def test_tick_after_the_set_changed_redraws(callbacks):
    status, out = draw(callbacks, TICK, **{IDS: "0:00000000", TICK: 1})
    assert status == 200
    assert "data" in out[FIG] and set(out) == {FIG, ORBITS, CAMERA, IDS}


def test_click_tracks_orbit_then_clear(callbacks, sample_df):
    click = {f"{OUT}.clickData": {"points": [{"curveNumber": 1, "pointNumber": 0}]}}
    status, out = draw(callbacks, f"{OUT}.clickData", **click)
    assert status == 200
    assert len(out[ORBITS]) == 1 and out[ORBITS][0] in set(sample_df.SatCatId)
    assert len(out[FIG]["data"]) == 4                             # + orbit path + current-position marker

    status, _ = draw(callbacks, f"{OUT}.clickData", **click, **{ORBITS: out[ORBITS]})
    assert status == 204                                          # clicking it again changes nothing

    status, cleared = draw(callbacks, "clear-orbits-btn.n_clicks",
                           **{ORBITS: out[ORBITS], "clear-orbits-btn.n_clicks": 1})
    assert status == 200 and cleared[ORBITS] == [] and len(cleared[FIG]["data"]) == 2


def test_click_off_a_satellite_does_nothing(callbacks):
    click = {f"{OUT}.clickData": {"points": [{"curveNumber": 0, "pointNumber": 0}]}}   # the Earth surface
    status, _ = draw(callbacks, f"{OUT}.clickData", **click)
    assert status == 204


@pytest.mark.parametrize("tab", ["2d-viz", "tbl-viz"])
def test_other_tabs_do_not_run_it(callbacks, tab):
    status, _ = draw(callbacks, **{"sat-viz-tabs.active_tab": tab})
    assert status == 204

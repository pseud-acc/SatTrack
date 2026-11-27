"""Callback tests: the 2D tab is built only while it is open (mount_2d in app/callbacks/callback_tabs.py; D-052).

Owner, 27 Nov 2026: every tab was rendered at once, so a phone ran the Plotly 3D scene and the 2D map behind the
globe. Opening the 2D tab builds the map for the current filters and starts its 3 s timer; any other tab removes the
map and stops the timer.
"""
import pytest

OUT = "tab-2d-body"
BODY, TIMER_OFF = f"{OUT}.children", "2d-viz-interval-component.disabled"


def test_opening_the_2d_tab_builds_the_map_and_starts_its_timer(callbacks):
    status, out = callbacks.call(OUT, "sat-viz-tabs.active_tab", **{"sat-viz-tabs.active_tab": "2d-viz"})
    assert status == 200
    graph = out[BODY][0]["props"]["children"][0]
    assert graph["props"]["id"] == "2d-earth-satellite-plot"
    assert graph["props"]["figure"]["data"], "the map is drawn for the current filters, not empty"
    assert out[TIMER_OFF] is False


@pytest.mark.parametrize("tab", ["globe", "tbl-viz"])
def test_other_tabs_hold_no_map_and_no_timer(callbacks, tab):
    status, out = callbacks.call(OUT, "sat-viz-tabs.active_tab", **{"sat-viz-tabs.active_tab": tab})
    assert status == 200
    assert out[BODY] == [] and out[TIMER_OFF] is True

"""Callback tests: the navigation bar (app/callbacks/callback_navbar.py), through /_dash-update-component.

Scope: the mobile menu button opens and closes the menu; the link for the current page is highlighted (the Explore
menu for its summary and every view), and any unknown path highlights Overview (the router shows the home page for
it).
"""
import pytest


def test_menu_button(callbacks):
    status, out = callbacks.call("navbar-collapse", "navbar-toggler.n_clicks",
                                 **{"navbar-toggler.n_clicks": 1, "navbar-collapse.is_open": False})
    assert status == 200 and out == {"navbar-collapse.is_open": True}
    _, out = callbacks.call("navbar-collapse", None, **{"navbar-toggler.n_clicks": None,
                                                        "navbar-collapse.is_open": False})
    assert out == {"navbar-collapse.is_open": False}


@pytest.mark.parametrize("path, active", [
    ("/", "home"), ("/sat_visualisation", "viz"), ("/no-such-page", "home"),
    ("/explore", "explore"), ("/explore/constellations", "explore"), ("/explore/", "explore"),
    ("/sources", "sources"), ("/faq", "faq"), ("/explorer", "home")])
def test_active_link(callbacks, path, active):
    status, out = callbacks.call("nav-home", "url.pathname", **{"url.pathname": path})
    assert status == 200
    assert out == {"nav-home.active": active == "home", "nav-viz.active": active == "viz",
                   "nav-explore.toggleClassName": "active" if active == "explore" else "",
                   "nav-sources.active": active == "sources", "nav-faq.active": active == "faq"}


def test_the_bar_has_the_five_destinations_and_the_explore_menu(callbacks):
    """Owner's N2 choice (28 Nov 2026): Overview, Tracker, Explore (a menu), Sources, FAQ; the menu lists the summary
    and the six views, each with a line saying what it is."""
    assert [callbacks.initial(i, "children") for i in ("nav-home", "nav-viz", "nav-sources", "nav-faq")] == [
        "Overview", "Tracker", "Sources", "FAQ"]
    assert [callbacks.initial(i, "href") for i in ("nav-home", "nav-viz", "nav-sources", "nav-faq")] == [
        "/", "/sat_visualisation", "/sources", "/faq"]
    assert callbacks.initial("nav-explore", "label") == "Explore"
    keys = ["summary", "constellations", "systems", "operators", "countries", "missions", "orbits"]
    hrefs = [callbacks.initial(f"nav-explore-{k}", "href") for k in keys]
    assert hrefs == ["/explore"] + [f"/explore/{k}" for k in keys[1:]]

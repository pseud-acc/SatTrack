"""Callback tests: the navigation bar (app/callbacks/callback_navbar.py), through /_dash-update-component.

Scope: the mobile menu button opens and closes the menu; the link for the current page is highlighted, and
any unknown path highlights Home (the router shows the home page for it).
"""
import pytest


def test_menu_button(callbacks):
    status, out = callbacks.call("navbar-collapse", "navbar-toggler.n_clicks",
                                 **{"navbar-toggler.n_clicks": 1, "navbar-collapse.is_open": False})
    assert status == 200 and out == {"navbar-collapse.is_open": True}
    _, out = callbacks.call("navbar-collapse", None, **{"navbar-toggler.n_clicks": None,
                                                        "navbar-collapse.is_open": False})
    assert out == {"navbar-collapse.is_open": False}


@pytest.mark.parametrize("path, home, viz", [
    ("/", True, False), ("/sat_visualisation", False, True), ("/no-such-page", True, False)])
def test_active_link(callbacks, path, home, viz):
    status, out = callbacks.call("nav-home", "url.pathname", **{"url.pathname": path})
    assert status == 200 and out == {"nav-home.active": home, "nav-viz.active": viz}

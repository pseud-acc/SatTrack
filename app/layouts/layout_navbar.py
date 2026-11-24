#!/usr/bin/env python

"""
The SatTrack top bar (D-044, roadmap 3.12): a compact 48 px bar with the brand, the page links and when the
satellite data was last updated. Collapses to a menu button on phones.

Function:
    create_navbar: the top bar component.

The ids navbar-toggler, navbar-collapse, nav-home and nav-viz are used by app/callbacks/callback_navbar.py and the
tests; keep them.
"""

## Packages
from dash import html
import dash_bootstrap_components as dbc

from app.core.state import get_app_data


def data_freshness():
    """'Data updated <time>' from the element sets' download time (the same value the tracker showed in its header),
    or None when the app data has no such value."""
    try:
        updated = get_app_data()["data"]["tle_metadata"]
    except Exception:   # the bar must render even if the data didn't load
        return None
    return f"Data updated {updated}" if updated else None


## --- Define Navbar layout ----
def create_navbar():
    """
    Creates the top bar.

    @return: dbc.Navbar component
    """
    freshness = data_freshness()
    status = html.Span(
        [html.Span(className="st-dot", **{"aria-hidden": "true"}), freshness],
        className="st-fresh d-none d-md-inline-flex",
        id="nav-freshness",
    ) if freshness else None

    navbar = dbc.Navbar(
        dbc.Container(
            [
                # Brand: a small orbit mark and the name
                html.A(
                    [html.Span(className="st-mark", **{"aria-hidden": "true"}), "SatTrack"],
                    href="/",
                    className="st-brand navbar-brand",
                ),

                # Menu button on phones
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0, className="st-toggler"),

                # Page links (collapsed into the menu on phones)
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Home", href="/", id="nav-home")),
                            dbc.NavItem(dbc.NavLink("Tracker", href="/sat_visualisation", id="nav-viz")),
                        ],
                        className="st-nav",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),

                status,
            ],
            fluid=True,
            className="st-topbar-inner",
        ),
        dark=True,
        className="st-topbar",
        sticky="top",
    )

    return navbar

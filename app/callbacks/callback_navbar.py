#!/usr/bin/env python

"""
This module defines dash app callbacks for the navbar.

Example:
        $ python callback_navbar.py

Functions:
    get_navbar_callbacks: wrapper function for navbar callbacks

Todo:
    *
"""

## Packages
from dash.dependencies import Input, Output, State


# Callback wrapper function
def page_for(pathname):
    """Which page a path shows (the router in run_app.py uses the same rule): tracker, explore (the summary and its
    views), sources, faq; anything else is the home page."""
    path = (pathname or "/").rstrip("/") or "/"
    if path == "/sat_visualisation":
        return "tracker"
    if path == "/explore" or path.startswith("/explore/"):
        return "explore"
    if path in ("/sources", "/faq"):
        return path[1:]
    return "home"


def register(app):
    '''
    Wrapper function that defines navbar callbacks using app instantiation.

    @param app: (dash app object) instantiated app object

    @return:
    '''

    # >>> Define Callbacks <

    '''
    ------------------------
    Navbar collapse toggle 
    -------------------------
    Interactive Inputs: navbar-toggler button clicks
    Outputs: navbar-collapse state (open/closed)
    '''

    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n_clicks, is_open):
        """
        Toggle the navbar collapse state when toggler is clicked.

        @param n_clicks: (int) number of times toggler has been clicked
        @param is_open: (bool) current state of navbar collapse

        @return: (bool) new state of navbar collapse
        """
        if n_clicks:
            return not is_open
        return is_open

    '''
    ------------------------
    Active page highlighting 
    -------------------------
    Interactive Inputs: URL pathname changes
    Outputs: active state for each nav link
    '''

    @app.callback(
        [
            Output("nav-home", "active"),
            Output("nav-viz", "active"),
            Output("nav-explore", "toggleClassName"),
            Output("nav-sources", "active"),
            Output("nav-faq", "active"),
        ],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        """
        Highlight the active navigation link based on current pathname.

        @param pathname: (str) current URL pathname

        @return: (tuple) active state for each nav link (home, viz)
        """
        page = page_for(pathname)
        return (page == "home", page == "tracker", "active" if page == "explore" else "", page == "sources",
                page == "faq")
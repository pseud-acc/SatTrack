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
            Output("nav-learn", "active")
        ],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        """
        Highlight the active navigation link based on current pathname.

        @param pathname: (str) current URL pathname

        @return: (tuple) active state for each nav link (home, viz, learn)
        """
        if pathname == "/":
            return True, False, False
        elif pathname == "/sat_visualisation":
            return False, True, False
        elif pathname == "/sat_applications":
            return False, False, True
        return False, False, False
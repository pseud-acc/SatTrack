#!/usr/bin/env python

"""
This module defines the navbar layout for the SatTrack app.

Example:
        $ python layout_navbar.py

Function:
    create_navbar: function to define navbar layout.

Todo:
    *
"""

## Packages
import dash_bootstrap_components as dbc


## --- Define Navbar layout ----
def create_navbar():
    """
    Creates the navigation bar layout.

    @return: dbc.Navbar component
    """

    navbar = dbc.Navbar(
        [
            dbc.Container(
                [
                    # Brand/Logo
                    dbc.NavbarBrand(
                        "SatTrack",
                        href="/",
                        className="ms-2 fs-4 fw-bold"
                    ),

                    # Toggler for mobile
                    dbc.NavbarToggler(
                        id="navbar-toggler",
                        n_clicks=0
                    ),

                    # Collapsible nav links
                    dbc.Collapse(
                        dbc.Nav(
                            [
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Home",
                                        href="/",
                                        id="nav-home"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Live Tracker",
                                        href="/sat_visualisation",
                                        id="nav-viz"
                                    )
                                ),
                                dbc.NavItem(
                                    dbc.NavLink(
                                        "Learn",
                                        href="/sat_applications",
                                        id="nav-learn"
                                    )
                                )
                            ],
                            className="ms-auto",
                            navbar=True,
                        ),
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                ],
                fluid=True,
            )
        ],
        color="dark",
        dark=True,
        className="mb-3",
        sticky="top",
    )

    return navbar
"""
Orbit type filter (LEO, MEO, GEO, GSO, HEO): a segmented control where any combination can be on (roadmap 3.3b,
Q3).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import DEFAULT_ORBITS


def create_orbit_filter(options):
    """
    Create the orbit type filter component.

    Args:
        options (dict): Dictionary containing orbit options

    Returns:
        html.Div: Orbit filter component
    """
    return html.Div([
        html.Label([
            "Orbit Type ",
            html.I(className="st-icon st-icon-info", id="orbit-info-icon")
        ], className="st-lbl"),
        dbc.Tooltip([
            html.Div([
                html.Strong("LEO:"), " Low Earth (160-2000km)", html.Br(),
                html.Strong("MEO:"), " Medium (2000-35786km)", html.Br(),
                html.Strong("GEO:"), " Geostationary (35786km)", html.Br(),
                html.Strong("GSO:"), " Geosynchronous", html.Br(),
                html.Strong("HEO:"), " Highly Elliptical"
            ], className="st-tip-body")
        ], target="orbit-info-icon", placement="right"),
        dcc.Checklist(
            options=[{"label": orbit, "value": orbit} for orbit in options["orbit"]],
            value=list(DEFAULT_ORBITS),   # every orbit class (owner, 26 Nov 2026; roadmap 3.3a)
            id="orbit-filter-checkbox",
            className="st-seg st-seg-multi mb-3",
            inline=True
        )
    ])

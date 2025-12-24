"""
Orbit type filter component (LEO, MEO, GEO, etc.).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


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
            html.I(className="fas fa-info-circle", id="orbit-info-icon",
                   style={'fontSize': '0.8rem', 'cursor': 'pointer'})
        ], className="fw-bold small"),
        dbc.Tooltip([
            html.Div([
                html.Strong("LEO:"), " Low Earth (160-2000km)", html.Br(),
                html.Strong("MEO:"), " Medium (2000-35786km)", html.Br(),
                html.Strong("GEO:"), " Geostationary (35786km)", html.Br(),
                html.Strong("GSO:"), " Geosynchronous", html.Br(),
                html.Strong("HEO:"), " Highly Elliptical"
            ], style={'textAlign': 'left'})
        ], target="orbit-info-icon", placement="right"),
        dcc.Checklist(
            options=[{"label": " " + orbit, "value": orbit} for orbit in options["orbit"]],
            value=["LEO", "GEO"],
            id="orbit-filter-checkbox",
            className="mb-3",
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fit, minmax(60px, 1fr))"},
            inputStyle={"marginRight": "5px"}
        )
    ])

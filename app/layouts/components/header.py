"""
Header component for satellite visualization page.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
from app.styles.styles_sat_visualisations import colours


def create_header(tle_update):
    """
    Create the header section with title and data source information.

    Args:
        tle_update (str): Last update timestamp from CelesTrak

    Returns:
        dbc.Row: Header component
    """
    return dbc.Row([
        dbc.Col([
            html.H1("Live Tracker",
                    className="text-center text-md-start mb-2",
                    style={'color': colours["ttext"], 'fontSize': 'clamp(1.5rem, 5vw, 2.5rem)'}),
            html.Div([
                html.Span("Real-time satellite tracking powered by ", className="d-block d-md-inline"),
                dcc.Link('CelesTrak', href='https://celestrak.com/', className="text-info"),
                html.Span(" • Last updated: " + tle_update, className="d-block d-md-inline text-muted")
            ], className="text-center text-md-start small")
        ])
    ], className="mb-3")

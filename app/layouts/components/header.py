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
        tle_update (str): Last update timestamp of the element sets

    Returns:
        dbc.Row: Header component
    """
    return dbc.Row([
        dbc.Col([
            html.H1("Live Tracker",
                    className="text-center text-md-start mb-2",
                    style={'color': colours["ttext"], 'fontSize': 'clamp(1.5rem, 5vw, 2.5rem)'}),
            html.Div(_source_credit() + [
                html.Span(" • Last updated: " + tle_update, className="d-block d-md-inline text-muted")
            ], className="text-center text-md-start small")
        ])
    ], className="mb-3")


def _source_credit():
    """Credit line for the data shown (Space-Track's terms require the USSPACECOM citation)."""
    return [
        html.Span("Real-time satellite tracking • Data: ", className="d-block d-md-inline"),
        dcc.Link('USSPACECOM via Space-Track.org', href='https://www.space-track.org/', className="text-info"),
        html.Span(" & "),
        dcc.Link('GCAT (J. McDowell)', href='https://planet4589.org/space/gcat/', className="text-info"),
    ]

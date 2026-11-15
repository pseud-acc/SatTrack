"""
Header component for satellite visualization page.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
from app.styles.styles_sat_visualisations import colours


def create_header(tle_update, data_source="github"):
    """
    Create the header section with title and data source information.

    Args:
        tle_update (str): Last update timestamp of the element sets
        data_source (str): 's3' (new pipeline: Space-Track + GCAT) or 'github' (legacy: CelesTrak),
            so the credit always names the source of the data actually shown

    Returns:
        dbc.Row: Header component
    """
    return dbc.Row([
        dbc.Col([
            html.H1("Live Tracker",
                    className="text-center text-md-start mb-2",
                    style={'color': colours["ttext"], 'fontSize': 'clamp(1.5rem, 5vw, 2.5rem)'}),
            html.Div(_source_credit(data_source) + [
                html.Span(" • Last updated: " + tle_update, className="d-block d-md-inline text-muted")
            ], className="text-center text-md-start small")
        ])
    ], className="mb-3")


def _source_credit(data_source):
    """Credit line for the data actually shown (Space-Track's terms require the USSPACECOM citation)."""
    if data_source == "s3":
        return [
            html.Span("Real-time satellite tracking • Data: ", className="d-block d-md-inline"),
            dcc.Link('USSPACECOM via Space-Track.org', href='https://www.space-track.org/', className="text-info"),
            html.Span(" & "),
            dcc.Link('GCAT (J. McDowell)', href='https://planet4589.org/space/gcat/', className="text-info"),
        ]
    return [
        html.Span("Real-time satellite tracking powered by ", className="d-block d-md-inline"),
        dcc.Link('CelesTrak', href='https://celestrak.com/', className="text-info"),
    ]

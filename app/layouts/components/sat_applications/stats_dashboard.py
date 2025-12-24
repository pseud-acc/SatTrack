"""
Statistics dashboard component showing key satellite metrics.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_stats_dashboard():
    """
    Create the statistics dashboard with key satellite metrics.

    Returns:
        dbc.Row: Statistics dashboard component
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("1957", className="text-info mb-0"),
                    html.P("First Satellite", className="text-muted small mb-0")
                ], className="text-center py-3")
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("15,000+", className="text-success mb-0"),
                    html.P("Active Today", className="text-muted small mb-0")
                ], className="text-center py-3")
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("100+", className="text-warning mb-0"),
                    html.P("Launches/Year", className="text-muted small mb-0")
                ], className="text-center py-3")
            ], className="shadow-sm")
        ], md=3, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("50+", className="text-danger mb-0"),
                    html.P("Countries", className="text-muted small mb-0")
                ], className="text-center py-3")
            ], className="shadow-sm")
        ], md=3, className="mb-3")
    ], className="mb-5")

"""
Navigation cards component for quick access to page sections.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_navigation_cards():
    """
    Create the section navigation cards.

    Returns:
        dbc.Row: Navigation cards component
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("History", className="card-title text-center"),
                    html.P("From Sputnik to modern constellations", className="card-text text-center small"),
                    dbc.Button("Explore", color="info", outline=True, size="sm",
                               href="#history", className="w-100")
                ])
            ], className="h-100 shadow-sm hover-card")
        ], md=3, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Applications", className="card-title text-center"),
                    html.P("Communications, navigation, and science", className="card-text text-center small"),
                    dbc.Button("Explore", color="success", outline=True, size="sm",
                               href="#applications", className="w-100")
                ])
            ], className="h-100 shadow-sm hover-card")
        ], md=3, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Launch Systems", className="card-title text-center"),
                    html.P("Rockets and orbital mechanics", className="card-text text-center small"),
                    dbc.Button("Explore", color="warning", outline=True, size="sm",
                               href="#launches", className="w-100")
                ])
            ], className="h-100 shadow-sm hover-card")
        ], md=3, className="mb-3"),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Ownership", className="card-title text-center"),
                    html.P("Who operates satellites today", className="card-text text-center small"),
                    dbc.Button("Explore", color="danger", outline=True, size="sm",
                               href="#owners", className="w-100")
                ])
            ], className="h-100 shadow-sm hover-card")
        ], md=3, className="mb-3")
    ], className="mb-5")

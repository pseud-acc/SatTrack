#!/usr/bin/env python

"""
SatTrack Development Server (v2)

This module runs the SatTrack App on a local development server with hot reload.
Uses the modularized callback registry for clean callback management.

Usage:
    $ python run_app_dev_v2.py

Features:
    - Multi-page navigation (Home, Visualizations, Applications)
    - Modular callback registration via callback_registry
    - Hot reload for development
    - Responsive mobile-first design
    - Component-based layout architecture

Pages:
    / (Home) - Landing page with feature overview
    /sat_visualisation - Live 3D/2D satellite tracking
    /sat_applications - Educational content about satellites

Todo:
    *
"""

## Packages

from dash import Dash, html, dcc, page_registry, page_container
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


## Internal Modules

# app data initialization
from app.core.state import get_app_data

# Callback registry
from app.callbacks.callback_registry import register_all_callbacks

# Layout components
from app.layouts.layout_navbar import create_navbar
from app.layouts.layout_home import create_dash_layout as create_dash_layout_home
from app.layouts.layout_sat_visualisations import create_dash_layout as create_dash_layout_sat_visualisations
from app.layouts.layout_sat_applications import create_dash_layout as create_dash_layout_sat_applications

## >>>>>>>> Initialize App <<<<<<<<<<<<

# Instantiate Dash App with Bootstrap theme
external_stylesheets = [
    dbc.themes.CYBORG,  # Dark theme for space-themed UI
    "https://use.fontawesome.com/releases/v5.15.4/css/all.css"  # Icons for filters and UI
]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1",
        }
    ]
)

# Reference underlying Flask server (for production deployment)
server = app.server

# Initialize app data (satellite catalog, filters, visualization configs)
app_data = get_app_data()

# Create persistent navigation bar
navbar = create_navbar()

# Define app layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # URL router component
    navbar,  # Persistent navigation bar
    html.Div(id='navbar-content'),  # Container for navbar state updates
    html.Div(id='page-content')  # Main content area (dynamically updated)
])

## >>>>>>>> Register Callbacks <<<<<<<<<<<<

# Register all callbacks using the centralized registry
# This includes: 3D viz, 2D viz, table, filters, navbar, home, and sat_applications
register_all_callbacks(app)


## >>>>>>>> Define Page Routing <<<<<<<<<<<<

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """
    Route URL pathname to appropriate page layout.

    Args:
        pathname (str): URL pathname from dcc.Location

    Returns:
        Dash component: Page layout corresponding to pathname

    Routes:
        / - Home page (landing/welcome)
        /sat_visualisation - Live satellite tracking (3D/2D/Table)
        /sat_applications - Educational content about satellites
    """
    if pathname == '/sat_visualisation':
        return create_dash_layout_sat_visualisations(app)
    elif pathname == '/sat_applications':
        return create_dash_layout_sat_applications(app)
    else:
        return create_dash_layout_home(app)


## >>>>>>>> Run Development Server <<<<<<<<<<<<

if __name__ == "__main__":
    app.run_server(
        port=8090,
        dev_tools_ui=True,
        dev_tools_hot_reload=True,
        threaded=True
    )
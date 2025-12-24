#!/usr/bin/env python

"""
SatTrack Production Server

This module runs the SatTrack App on a production server.

Usage:
    $ python run_app.py

Features:
    - Production-ready satellite visualization
    - Google Analytics integration
    - Optimized for Heroku deployment

Todo:
    *

"""

## Packages

import pandas as pd
from dash import Dash
import dash_bootstrap_components as dbc

## Internal Modules

# app data initialization
from app.core.state import get_app_data

# Callback registry
from app.callbacks.callback_registry import register_all_callbacks

# Layout components
from app.layouts.layout_navbar import create_navbar
from app.layouts.layout_home import create_dash_layout as create_dash_layout_home
from app.layouts.layout_sat_visualisations import create_dash_layout as create_dash_layout_sat_visualisations

## >>>>>>>> Initialize App <<<<<<<<<<<<

# Instantiate Dash App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Google Analytics
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-LF4EP2J2F8"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'G-LF4EP2J2F8');
        </script>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

## >>>>>>>> Initialize App Data <<<<<<<<<<<<

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

## >>>>>>>> Define Page Routing + Layouts <<<<<<<<<<<<

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
    """
    if pathname == '/sat_visualisation':
        return create_dash_layout_sat_visualisations(app)
    else:
        return create_dash_layout_home(app)


## >>>>>>>> Run App <<<<<<<<<<<<

if __name__ == "__main__": 
    app.run_server(
        debug=False, 
        host='0.0.0.0', 
        port=8050)

#!/usr/bin/env python

"""

This module runs the SatTrack App on a local (development) server.

Example:

        $ python app.py

Attributes:

Todo:
    *

"""

## Packages

from dash import Dash, html, dcc, page_registry, page_container
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output


## Internal Modules

# navigation bar
from app.components.navbar import navbar, update_navbar

# app home page layout + callback
from app.layouts.layout_home import create_dash_layout as create_dash_layout_home
from app.callbacks.callback_home import get_callbacks as get_callbacks_home

# sat visualisations layout + callback
from app.layouts.layout_sat_visualisations import create_dash_layout as create_dash_layout_sat_visualisations
from app.callbacks.callback_sat_visualisations import get_callbacks as get_callbacks_sat_visualisations

# sat science layout + callback

# sat applications layout + callback
from app.layouts.layout_sat_applications_old_v2 import create_dash_layout as create_dash_layout_sat_applications
from app.callbacks.callback_sat_applications import get_callbacks as get_callbacks_sat_applications

## >>>>>>>> Create App <<<<<<<<<<<<

# Instantiate  App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__,
           external_stylesheets=external_stylesheets,
           meta_tags=[
               {
                   "name": "viewport",
                   "content": "width=device-width, initial-scale=1, maximum-scale=1",
               }]
           )

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku)
#server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/')


# Include navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,  # Navigation bar
    html.Div(id='navbar-content'),  # This div will be updated by the callback
    html.Div(id='page-content')
])

# Register callbacks for different pages
get_callbacks_home(app)
get_callbacks_sat_visualisations(app)
get_callbacks_sat_applications(app)
update_navbar(app)

# Define the callback to update the page content based on the URL
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/sat_visualisation':
        return create_dash_layout_sat_visualisations(app)
    elif pathname == '/sat_applications':
        return create_dash_layout_sat_applications(app)
    else:
        return create_dash_layout_home(app)

## >>>>>>>> Run App <<<<<<<<<<<<

app.run_server(port = 8090, dev_tools_ui=True, #debug=True,
              dev_tools_hot_reload =True, threaded=True)

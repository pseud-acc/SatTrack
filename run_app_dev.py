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

import pandas as pd
from dash import Dash
import dash_bootstrap_components as dbc
import sys

## Internal Scripts

# helper scrips
from app.helper.initialise_app import (import_data, filter_setup, initialise_2d, initialise_3d_ls)
# app layout
from app.layouts.layout_sat_visualisations import create_dash_layout
# app callbacks
from app.callbacks.callback_sat_visualisations import get_callbacks

## >>>>>>>> Initilise App <<<<<<<<<<<<

# Instantiate  App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
#server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

## >>>>>>>> Setup App Inputs <<<<<<<<<<<<

# Import Data
"""
    Dynamic Satellite catalogue data - contains TLEs
"""
satcat_loc = "./dat/clean/satcat_tle.csv"

"""
    Greyscale Earth Map
"""
img_loc = "./app/assets/images/gray_scale_earth_2048_1024.jpg"
resolution = 8
df, img, radius_earth = import_data(satcat_loc, img_loc, resolution)

# Initialise Filter 
options, input_filter, tbl_col_map = filter_setup(df)

# Initilise Visualisations
surf_3d, layout_3d, fig3d_0 = initialise_3d_ls(df, img)
scatter_2d, layout_2d, fig2d_0  = initialise_2d()

# Import metadata
metadata_loc = "./dat/meta/last_data_update.csv"
metadata = pd.read_csv(metadata_loc)
tle_update = metadata[metadata["Source"]=="Celestrak_TLE"]["Last Update"].values[0]


## >>>>>>>> Create App Layout <<<<<<<<<<<<

create_dash_layout(app = app,
                   tle_update_in = tle_update,
                   options_in = options,
                   fig3d_0_in = fig3d_0,
                   fig2d_0_in = fig2d_0,
                   tbl_col_map_in = tbl_col_map);


## >>>>>>>> Define App Interactivity <<<<<<<<<<<<

# import callback functions
get_callbacks(app = app,
              df_in = df,
              input_filter_in = input_filter,
              surf_3d_in = surf_3d,
              fig3d_0_in = fig3d_0,
              layout_3d_in = layout_3d,
              layout_2d_in = layout_2d,
              tbl_col_map_in = tbl_col_map)

## >>>>>>>> Run App <<<<<<<<<<<<

app.run_server(port = 8090, dev_tools_ui=True, #debug=True,
              dev_tools_hot_reload =True, threaded=True)

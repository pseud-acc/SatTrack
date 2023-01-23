#!/usr/bin/env python

"""

This module runs the SatTrack App on a production server.

Example:

        $ python app.py

Attributes:

Todo:
    *

"""

import sys
import os
sys.path.append("./src/app/")
sys.path.append("./src/helper/")

# 3rd party packages

import pandas as pd
import numpy as np
import json

import gunicorn # To run app on Heroku

import plotly.express as px # Packgaes to generate interactivity
import dash_vtk
from dash import Dash
import dash_bootstrap_components as dbc

# internal packages

from celestial_geometry_funs import compute_satloc, lla_to_xyz, sphere 
from app_settings import *
from initialise_app import (import_data, filter_setup, initialise_2d, initialise_3d, initialise_3d_ls)
from app_layout import create_dash_layout
from app_callbacks import get_callbacks

## >>>>>>>> Initilise App <<<<<<<<<<<<

# Instantiate  App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Google analytics
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



## >>>>>>>> Setup App Inputs <<<<<<<<<<<<

# Import Data
"""
    Dynamic Satellite catalogue data - contains TLEs
"""
satcat_loc = "./dat/clean/satcat_tle.csv"

"""
    Greyscale Earth Map
"""
img_loc = "./static/gray_scale_earth_2048_1024.jpg"
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

if __name__ == "__main__": app.run_server(debug=False, host='0.0.0.0', port=8050)

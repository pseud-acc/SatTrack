#!/usr/bin/env python

"""

This module initialises data used in the app

Example:

        $ python initialise_app_data.py

Function:
    create_dash_layout: function to define dash app layout.
Todo:
    *

"""
## Packages

import pandas as pd
import sys

## Internal Modules
sys.path.append("../../")

# user config
from app.config.user_setup_app import (satcat_loc, img_loc, metadata_loc, resolution)
# helper scripts
from app.helper.initialise_app import (import_data, filter_setup, initialise_2d, initialise_3d_ls)


"""
    Import Data
"""
# Import data for visualisations
df, img, radius_earth = import_data(satcat_loc, img_loc, resolution)

# Import Metadata
#metadata = pd.read_csv(metadata_loc) 
metadata = pd.read_csv('https://raw.githubusercontent.com/pseud-acc/SatTrack/refs/heads/main/dat/meta/last_data_update.csv')
tle_update = metadata[metadata["Source"]=="Celestrak_TLE"]["Last Update"].values[0]

"""
    Import App Features
"""
# Initialise Filter
options, input_filter, tbl_col_map = filter_setup(df)


# Initilise Visualisations
surf_3d, layout_3d, fig3d_0 = initialise_3d_ls(df, img)
scatter_2d, layout_2d, fig2d_0 = initialise_2d()


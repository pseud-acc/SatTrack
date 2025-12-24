#!/usr/bin/env python

"""

This module initialises app state data used in the app 

Example:

        $ python state.py

Functions:
    import_data: Import satellite data and earth map
    initialise_app_data: Run functions to initialise app
    get_app_data: Get cached app data
    clear_app_data_cache: Clear cached app data
Todo:
    *

"""
## Packages
import pandas as pd
import sys
import numpy as np
from PIL import Image

## Internal Modules
sys.path.append("../../")
# user config
from app.config.user_setup_app import (satcat_loc, img_loc, metadata_loc)
# helper scripts
from app.helper.helper__constants import _resolution_3d_earth_map__c
from app.helper.helper__plot_display import (create_3d_layout, create_3d_surface, create_3d_figure, 
                                             create_2d_layout, create_2d_figure)
from app.helper.helper__table_display import create_table_mapping
from app.helper.helper__app_data import create_data_filters

# Global cache for app data (lazy initialization)
_app_data_cache = None

def import_app_data(satcat_loc, img_loc, metadata_loc, res):
    '''
    Import satellite data and earth map.

    @param satcat_loc: dynamic location of satellite data
    @param img_loc: static location of Earth map
    @param metadata_loc: dynamic location of TLE metadata
    @param res: integer - Earth map resolution in increments of 2^x for integer x
    @return satcat:  dataframe of satellite data
    @return img_compr:  compressed image array of Earth map
    @return tbl_col_map: dict of column name mapping for table export
    '''

    ## Satellite catalogue data - contains TLEs

    satcat = pd.read_csv(satcat_loc)
    # satcat = pd.read_csv('https://raw.githubusercontent.com/pseud-acc/SatTrack/refs/heads/main/dat/clean/satcat_tle.csv')
    print("Satellite catalgoue and TLE data successfully imported!")

    # Import TLE download metadata
    metadata = pd.read_csv(metadata_loc)
    tle_metadata = metadata[metadata["Source"]=="Celestrak_TLE"]["Last Update"].values[0]
    print("TLE metadata successfully imported!")    

    img = np.asarray(Image.open(img_loc))
    print("Earth Map successfully imported!")
    # url = 'https://raw.githubusercontent.com/pseud-acc/SatTrack/refs/heads/main/static/gray_scale_earth_2048_1024.jpg'
    # response = requests.get(url)
    # img = np.asarray(Image.open((BytesIO(response.content))))
    img = img.T
    # Compress image
    img_compr = img[0:-1:res,0:-1:res]

    return satcat, img_compr, tle_metadata

def initialise_app_data():
    '''
        Run functions to initialise app
    '''

    print("Initialising app data...")
    # Import data for visualisations
    df, img, tle_metadata = import_app_data(satcat_loc, img_loc, metadata_loc, _resolution_3d_earth_map__c)

    # Logging - to replace print w/ logging module later
    print(f" - Satellite catalogue size: {df.shape}")
    print(f" - Earth map size (compressed): {img.shape}")
    print(f" - TLE metadata: {tle_metadata}")

    # Initialise Filters
    options, initial_filter = create_data_filters(df)

    # Initilise Visualisations
    surf_3d = create_3d_surface(img)
    layout_3d = create_3d_layout()
    figure_3d = create_3d_figure(layout_3d, surf_3d)
    layout_2d = create_2d_layout()
    figure_2d = create_2d_figure(layout_2d)

    # Define table column mapping
    tbl_column_map = create_table_mapping()

    # Store app data in dictionary
    app_data = dict()

    # Satellite Visualisation Data
    app_data['data'] = dict()
    app_data['data']['satcat_df'] = df
    app_data['data']['tle_metadata'] = tle_metadata
    app_data['data']['tbl_col_map'] = tbl_column_map

    # Visualisation filters
    app_data['filter'] = dict()
    app_data['filter']['options'] = options
    app_data['filter']['initial_filter'] = initial_filter
    # 3D Visualisation
    app_data['viz_3d'] = dict()
    app_data['viz_3d']['surface'] = surf_3d
    app_data['viz_3d']['layout'] = layout_3d
    app_data['viz_3d']['base_figure'] = figure_3d
    # 2D Visualisation
    app_data['viz_2d'] = dict()
    app_data['viz_2d']['layout'] = layout_2d
    app_data['viz_2d']['base_figure'] = figure_2d

    return app_data

def get_app_data():
    """Lazy initialization singleton"""
    global _app_data_cache
    if _app_data_cache is None:
        _app_data_cache = initialise_app_data()
    return _app_data_cache

def clear_app_data_cache():
    """Force reinitialization (useful for testing or data reload)"""
    global _app_data_cache
    _app_data_cache = None

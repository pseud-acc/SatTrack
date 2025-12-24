#!/usr/bin/env python

"""

This module defines dash app callbacks used in the SatTrack visualisation.

Example:

        $ python callback_sat_visualisations.py

Functions:
    get_callbacks: wrapper function for callbacks
    update_3dviz: callback function for interactive 3d satellite visualisation
    update_2dviz: callback function for interactive 2d satellite visualisation
    update_tbl: callback function for table of satellites
    update_dropdown: callback function for satellite name and satcat number dynamic filter dropdown options

Todo:
    * 

"""

## Packages

import sys
import numpy as np
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import Dash, callback_context


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import (filter_satellite_data)
from app.helper.helper__filter_display import (sort_filter_dropdown_options, format_year_slider_output)


# Callback wrapper function
def register(app):
    ''' 
    Wrapper function that defines callbacks using app instantiation.

    @param app: (dash app object) instantiated app object

    '''

    # Get app data
    app_data = get_app_data()
    df = app_data['data']['satcat_df']
    input_filter = app_data['filter']['initial_filter']

    # >>> Define Callbacks <<<

    '''
    ------------------------
    Dynamic dropdown 
    -------------------------
    Interactive Inputs: Filter dropdowns, Launch year slider
    Outputs: Satellite name and SATCAT number filter dropdown options
    '''

    @app.callback(
        [
            Output('satname-filter-dropdown', 'options'),
            Output('satcatid-filter-dropdown', 'options'),
            Output('satname-filter-dropdown', 'value'),
            Output('satcatid-filter-dropdown', 'value')
        ],
        [
            Input('status-filter-checkbox', 'value'),
            Input('orbit-filter-checkbox', 'value'),
            Input('satname-filter-dropdown', 'value'),
            Input('satcatid-filter-dropdown', 'value'),
            Input('owner-filter-multi-dropdown', 'value'),
            Input('launchvehicle-filter-multi-dropdown', 'value'),
            Input('purpose-filter-multi-dropdown', 'value'),
            Input('launchyear-filter-slider', 'value')
        ]
    )
    def update_dropdown(status, orbit, satname, satcatid,
                        owner, launchvehicle,
                        purpose, year):

        # Filter data using helper
        dff, _, _ = filter_satellite_data(df, input_filter,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        if dff.shape[0] == 0:
            satname = None
            satcatid = None
            dff, _, _ = filter_satellite_data(df, input_filter,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        else:
            dff, _, _ = filter_satellite_data(df, input_filter,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        
        # Format dropdown options
        satname_options, satcatid_options = sort_filter_dropdown_options(dff)

        return satname_options, satcatid_options, satname, satcatid

    '''
    ------------------------
    Year range display
    -------------------------
    Interactive Inputs: Launch year slider
    Outputs: Year range text display
    '''

    @app.callback(
        Output('year-range-display', 'children'),
        Input('launchyear-filter-slider', 'value')
    )
    def update_year_display(year_range):
        """
        Display the currently selected year range.

        @param year_range: (list) [min_year, max_year]

        @return: (str) formatted year range text
        """
        if year_range:
            return f"{year_range[0]} - {year_range[1]}"
        return "All Years"

    '''
    ------------------------
    Launch Year Display Update
    -------------------------
    Updates the min/max year display bubbles when slider changes
    '''

    @app.callback(
        [
            Output('launch-year-min-display', 'children'),
            Output('launch-year-max-display', 'children')
        ],
        Input('launchyear-filter-slider', 'value')
    )
    def update_year_display(year_range):

        # define year output


        if year_range:
            return format_year_slider_output('min', year_range[0]), format_year_slider_output('max', year_range[1])
        return format_year_slider_output('min', options["launchyear"][0]), format_year_slider_output('max', options["launchyear"][-1])

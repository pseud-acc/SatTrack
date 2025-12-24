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
# app helper functions
from app.helper.helper__table_display import (format_table_data)


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
    Table visualisation 
    -------------------------
    Interactive Inputs: Filter dropdowns, Launch year slider, update time button
    Outputs: Table of satellites
    '''

    @app.callback(
        Output('satellite-list', 'data'),
        [
            Input('status-filter-checkbox', 'value'),
            Input('orbit-filter-checkbox', 'value'),
            Input('satname-filter-dropdown', 'value'),
            Input('satcatid-filter-dropdown', 'value'),
            Input('owner-filter-multi-dropdown', 'value'),
            Input('launchvehicle-filter-multi-dropdown', 'value'),
            Input('purpose-filter-multi-dropdown', 'value'),
            Input('launchyear-filter-slider', 'value'),
            Input("sat-viz-tabs", "active_tab"),
            Input("time-update-btn", "n_clicks")
        ]
    )
    def update_tbl(status, orbit, satname, satcatid,
                   owner, launchvehicle,
                   purpose, year, tab, update_time_btn):

        if tab != "tbl-viz":
            raise PreventUpdate
        elif tab == "tbl-viz":

            # Filter data using helper
            dff, time_now, _ = filter_satellite_data(df, input_filter,
                                                          status, orbit, satname,
                                                            satcatid, owner,
                                                            launchvehicle, purpose, year)
            # Table output
            table_data = format_table_data(dff, time_now)

            return table_data

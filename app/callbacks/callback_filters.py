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
    filter_table = app_data['filter']['table']

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
        dff, _, _ = filter_satellite_data(df, filter_table,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        if dff.shape[0] == 0:
            satname = None
            satcatid = None
            dff, _, _ = filter_satellite_data(df, filter_table,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        else:
            dff, _, _ = filter_satellite_data(df, filter_table,
                                        status, orbit, satname, satcatid,
                                        owner, launchvehicle, purpose, year)
        
        # Format dropdown options
        satname_options, satcatid_options = sort_filter_dropdown_options(dff)

        return satname_options, satcatid_options, satname, satcatid

    '''------------------------
    Mobile responsiveness
    -------------------------
    Interactive Inputs: Toggle filter button
    Outputs: Filter collapse state and icon rotation
    '''

    @app.callback(
        [
            Output("filter-collapse", "is_open"),
            Output("toggle-icon", "className")
        ],
        [Input("toggle-filters", "n_clicks")],
        [State("filter-collapse", "is_open")]
    )
    def toggle_filters(n, is_open):
        if n:
            new_state = not is_open
            icon_class = "st-icon st-icon-chevron-up" if new_state else "st-icon st-icon-chevron-down"
            return new_state, icon_class
        # Initial state: filters are collapsed, so show down chevron
        return is_open, "st-icon st-icon-chevron-down"        

    '''------------------------
    Desktop panel strip (3.12 step 3)
    -------------------------
    Interactive Inputs: the panel's fold button
    Outputs: the tracker row's class (st-panel-folded narrows the panel to a strip; assets/04_shell.css) and the icon
    '''

    @app.callback(
        [
            Output("tracker-row", "className"),
            Output("panel-strip-icon", "className")
        ],
        [Input("panel-strip-toggle", "n_clicks")],
        [State("tracker-row", "className")],
        prevent_initial_call=True
    )
    def toggle_panel_strip(n, row_class):
        classes = (row_class or "").split()
        folded = "st-panel-folded" not in classes
        classes = [c for c in classes if c != "st-panel-folded"] + (["st-panel-folded"] if folded else [])
        icon = "st-icon st-icon-chevron-right" if folded else "st-icon st-icon-chevron-left"
        return " ".join(classes), icon


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
    def update_min_max_year_display(year_range):

        # define year output


        if not year_range:
            raise PreventUpdate   # no slider value: keep the labels as they are
        return format_year_slider_output('min', year_range[0]), format_year_slider_output('max', year_range[1])

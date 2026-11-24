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
from dash import Dash, callback_context, no_update


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import (filter_satellite_data)
from app.helper.helper__filter_display import (search_options, format_year_slider_output)


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
    Search dropdowns (server-side search)
    -------------------------
    Interactive Inputs: the sidebar filters, the two dropdowns' values and what is typed in them (search_value)
    Outputs: the dropdowns' options (at most 50 matches each, see search_options) and, only when a filter change
    means the selection no longer matches, the cleared values. Otherwise the values are left alone (no_update), so
    typing in a search box never redraws the figures.
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
            Input('launchyear-filter-slider', 'value'),
            Input('satname-filter-dropdown', 'search_value'),
            Input('satcatid-filter-dropdown', 'search_value')
        ]
    )
    def update_dropdown(status, orbit, satname, satcatid,
                        owner, launchvehicle,
                        purpose, year, name_search, id_search):

        # A selection that no longer matches the other filters is cleared
        clear = False
        if satname or satcatid:
            selected, _, _ = filter_satellite_data(df, filter_table,
                                                status, orbit, satname, satcatid,
                                                owner, launchvehicle, purpose, year)
            clear = selected.shape[0] == 0
        if clear:
            satname, satcatid = None, None

        # Options: matches for what is typed, among the satellites the other filters allow
        dff, _, _ = filter_satellite_data(df, filter_table,
                                        status, orbit, None, None,
                                        owner, launchvehicle, purpose, year)
        satname_options, satcatid_options = search_options(dff, name_search, id_search, satname, satcatid)

        if clear:
            return satname_options, satcatid_options, None, None
        return satname_options, satcatid_options, no_update, no_update

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
            icon_class = "fas fa-chevron-up" if new_state else "fas fa-chevron-down"
            return new_state, icon_class
        # Initial state: filters are collapsed, so show down chevron
        return is_open, "fas fa-chevron-down"        


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

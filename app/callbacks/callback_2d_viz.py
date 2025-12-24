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
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import (filter_satellite_data)
# app helper functions
from app.helper.helper__plot_display import (create_2d_scatter_plot, create_2d_figure)


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
    layout_2d = app_data['viz_2d']['layout']


    # >>> Define Callbacks <<<

    '''
    ------------------------
    2d visualisation 
    -------------------------
    Interactive Inputs: Filter dropdowns, Launch year slider, update time button, interval-timer
    Outputs: 2d orbit path scatter plot
    '''

    @app.callback(
        Output('2d-earth-satellite-plot', 'figure'),
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
            Input("time-update-btn", "n_clicks"),
            Input('2d-viz-interval-component', "n_intervals")
        ]
    )
    def update_2dviz(status, orbit, satname, satcatid,
                     owner, launchvehicle,
                     purpose, year, tab, update_time_btn, time_intverval):

        if tab != "2d-viz":
            raise PreventUpdate
        elif tab == "2d-viz":

            # Filter data using helper
            dff, time_now, _ = filter_satellite_data(df, input_filter,
                                                          status, orbit, satname, 
                                                          satcatid, owner, 
                                                          launchvehicle, purpose, year)

            ## 2D Visualisation
            # Create 2D orbit path scatter plot
            scatter_plots = create_2d_scatter_plot(dff, time_now)
            # Create 2D figure
            fig_2d = create_2d_figure(layout_2d, scatter_plots)


            return fig_2d

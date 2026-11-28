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
from app.helper.helper__app_data import list_objects
# app helper functions
from app.helper.helper__table_display import (format_table_data)
from app.layouts.components.visualizations.viz_table import create_table_body


# Callback wrapper function
def register(app):
    ''' 
    Wrapper function that defines callbacks using app instantiation.

    @param app: (dash app object) instantiated app object 
    '''

    # Get app data
    app_data = get_app_data()
    objects_df = app_data['data']['objects_df']   # every object type (owner, 27 Nov 2026)
    filter_table = app_data['filter']['table']
    tbl_col_map = app_data['data']['tbl_col_map']

    # >>> Define Callbacks <<<
    '''
    ------------------------
    Table visualisation
    -------------------------
    The list tab's table is built only while the tab is open (D-052): the first time it opens, and again when the
    filters change while it's open or have changed since it was last shown (`list-shown-spec`). Opening the tab with
    unchanged filters sends nothing, so switching tabs doesn't resend ~4 MB of rows.
    Inputs: the open tab, the filter-spec store (roadmap 3.3a)
    Outputs: the list tab's contents and the spec they were built for
    '''

    @app.callback(
        Output("tab-list-body", "children"),
        Output("list-shown-spec", "data"),
        Input("sat-viz-tabs", "active_tab"),
        Input("filter-spec", "data"),   # the panel's filter spec (roadmap 3.3a, Q7)
        State("list-shown-spec", "data"),
    )
    def update_tbl(tab, spec, shown):
        if tab != "tbl-viz" or shown == {"spec": spec}:
            raise PreventUpdate
        dff, time_now = list_objects(objects_df, filter_table, spec)
        return create_table_body(tbl_col_map, format_table_data(dff, time_now)), {"spec": spec}

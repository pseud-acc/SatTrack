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
from dash import Dash, callback_context, ctx, no_update


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import (filter_satellite_data, sidebar_filter_spec, OBJECT_TYPES, JUNK_TYPES)
from app.core import filter_spec as spec_rules
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

        # The search lists follow the other filters (not the type switches: the app CSV holds payloads only).
        # Unchanged in 3.3a: 3.3b sets the lists once at load (Q8). It keeps its own inputs because it also writes the
        # name and SATCAT values, which feed the filter-spec store (reading the store here would make a cycle).
        def rows(name, catid):
            spec = sidebar_filter_spec(status, orbit, name, catid, owner, launchvehicle, purpose, year)
            return filter_satellite_data(df, filter_table, spec)[0]
        dff = rows(satname, satcatid)
        if dff.shape[0] == 0:
            satname = None
            satcatid = None
            dff = rows(satname, satcatid)
        
        # Format dropdown options
        satname_options, satcatid_options = sort_filter_dropdown_options(dff)

        return satname_options, satcatid_options, satname, satcatid

    '''------------------------
    The filter spec (roadmap 3.3a)
    -------------------------
    Interactive Inputs: every panel control
    Outputs: the page's filter-spec store, which the globe, Plotly 3D and 2D and the list read (Q7). The page renders
    the starting spec into the store, so nothing runs at load.
    '''

    @app.callback(
        Output('filter-spec', 'data'),
        [
            Input('status-filter-checkbox', 'value'),
            Input('orbit-filter-checkbox', 'value'),
            Input('satname-filter-dropdown', 'value'),
            Input('satcatid-filter-dropdown', 'value'),
            Input('owner-filter-multi-dropdown', 'value'),
            Input('launchvehicle-filter-multi-dropdown', 'value'),
            Input('purpose-filter-multi-dropdown', 'value'),
            Input('launchyear-filter-slider', 'value'),
            Input('type-filter-checkbox', 'value'),
        ],
        prevent_initial_call=True
    )
    def update_filter_spec(status, orbit, satname, satcatid, owner, launchvehicle, purpose, year, types):
        spec = sidebar_filter_spec(status, orbit, satname, satcatid, owner or [], launchvehicle or [], purpose or [],
                                   year, types or [])
        return None if spec is None else spec_rules.validate(spec)

    '''------------------------
    Space junk mode (roadmap 3.3a; owner, 26 Nov 2026)
    -------------------------
    Interactive Inputs: the junk switch, the type switches
    Outputs: the switch, the types, the status and the status to restore
    Almost all rocket bodies and debris are Inactive, so junk mode on also ticks Inactive (remembering the status before);
    off restores it. Ticking both junk types by hand turns the switch on, unticking either turns it off; neither
    touches the status.
    '''

    @app.callback(
        [
            Output('junk-mode-switch', 'value'),
            Output('type-filter-checkbox', 'value'),
            Output('status-filter-checkbox', 'value'),
            Output('status-before-junk', 'data'),
        ],
        [
            Input('junk-mode-switch', 'value'),
            Input('type-filter-checkbox', 'value'),
        ],
        [
            State('status-filter-checkbox', 'value'),
            State('status-before-junk', 'data'),
        ],
        prevent_initial_call=True
    )
    def junk_mode(junk, types, status, status_before):
        types, status = list(types or []), list(status or [])
        if ctx.triggered_id == 'junk-mode-switch':
            if junk:
                types = [t for t in OBJECT_TYPES if t in types or t in JUNK_TYPES]
                new_status = [s for s in ("Active", "Inactive") if s in status or s == "Inactive"]
                return no_update, types, new_status, status
            types = [t for t in types if t not in JUNK_TYPES]
            return no_update, types, (status_before if status_before is not None else status), None
        both = all(t in types for t in JUNK_TYPES)
        if bool(junk) == both:
            raise PreventUpdate
        return both, no_update, no_update, (no_update if both else None)

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

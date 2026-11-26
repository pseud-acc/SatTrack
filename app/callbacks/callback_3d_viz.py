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
from dash import Dash, Patch, callback_context, no_update


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import (filter_satellite_data)
# app helper functions
from app.helper.helper__plot_display import (create_3d_scatter_plot, create_3d_figure, 
                                            annotate_3d_figure, update_3d_camera_view,
                                            add_orbit_paths_to_figure, handle_orbit_click,
                                            annotation_3d_text, create_orbit_traces,
                                            satellite_ids_signature, scatter_3d_position_text,
                                            scatter_3d_xyz)

TICK = '3d-viz-interval-component.n_intervals'


# Callback wrapper function
def register(app):
    ''' 
    Wrapper function that defines callbacks using app instantiation.

    @param app: (dash app object) instantiated app object

    @return:    
    '''

    # Get app data
    app_data = get_app_data()
    df = app_data['data']['satcat_df']
    filter_table = app_data['filter']['table']
    surf_3d = app_data['viz_3d']['surface']
    layout_3d = app_data['viz_3d']['layout']
    fig3d_0 = app_data['viz_3d']['base_figure']

    # >>> Define Callbacks <<<

    '''
    ------------------------
    3d visualisation 
    -------------------------
    Interactive Inputs: the filter-spec store (roadmap 3.3a), plot clicks, update time button, interval-timer
    Outputs: 3d Satellite scatter plot, 3d orbit line plot, camera view
    '''

    @app.callback(
        [
            Output('3d-earth-satellite-plot', 'figure'),
            Output('3d-orbit-memory', 'data'),
            Output('camera-memory', "data"),
            Output('3d-sat-ids', 'data')
        ],
        [
            Input('filter-spec', 'data'),   # the panel's filter spec (roadmap 3.3a, Q7)
            Input("3d-earth-satellite-plot", "clickData"),
            Input('3d-orbit-memory', 'data'),
            Input("sat-viz-tabs", "active_tab"),
            Input("clear-orbits-btn", "n_clicks"),
            Input('3d-viz-interval-component', "n_intervals")
        ],
        State('camera-memory', "data"),
        State('3d-earth-satellite-plot', 'relayoutData'),
        State('3d-sat-ids', 'data')
    )
    def update_3dviz(spec,
                     clickData, orbit_list, tab,
                     clear_orbits_btn, time_interval, 
                     cam_mem, cam_scene, sat_ids_shown):

        if tab != "3d-viz":
            raise PreventUpdate
        elif tab == "3d-viz":
            # Filter data using helper
            dff, time_now, sat_status_enc = filter_satellite_data(df, filter_table, spec)

            sat_ids = satellite_ids_signature(dff)

            # Timer tick with the same satellites already drawn: send only what moved (positions, the
            # position text in the hover labels, the timestamp, orbit paths). The Earth surface, hover
            # template, per-satellite hover values and camera stay as they are in the browser.
            triggered = [t["prop_id"] for t in callback_context.triggered]
            if triggered == [TICK] and sat_ids == sat_ids_shown:
                patch = Patch()
                x, y, z = scatter_3d_xyz(dff)
                patch["data"][1]["x"] = x
                patch["data"][1]["y"] = y
                patch["data"][1]["z"] = z
                patch["data"][1]["text"] = scatter_3d_position_text(dff)
                patch["layout"]["annotations"][0]["text"] = annotation_3d_text(dff, time_now)
                # Keep the user's view: the patched figure still holds the camera of the last full draw,
                # so re-apply the latest rotation/zoom, as update_3d_camera_view does on a full draw.
                camera = (cam_scene or {}).get("scene.camera") or (cam_mem or {}).get("scene.camera")
                if camera:
                    patch["layout"]["scene"]["camera"] = camera
                for i, trace in enumerate(create_orbit_traces(dff, orbit_list or [], time_now)):
                    patch["data"][2 + i] = trace.to_plotly_json()
                return patch, no_update, no_update, no_update

            # Update orbit list based on clicks
            orbit_list_updated = handle_orbit_click(callback_context, clickData, orbit_list, dff)                                                          

            ## Generate 3d figure

            # Create scatter plot for active/inactive satellites
            scatter_3d = create_3d_scatter_plot(dff, sat_status_enc)
            # Create base 3d figure
            fig_3d = create_3d_figure(layout_3d, surf_3d, scatter_3d)
            # Annotate 3d figure
            fig_3d = annotate_3d_figure(fig_3d, dff, time_now)

            # Update 3d camera view
            fig_3d, cam_mem = update_3d_camera_view(cam_mem, cam_scene, fig_3d)

            # Add orbit paths to figure
            fig_3d = add_orbit_paths_to_figure(fig_3d, dff, orbit_list_updated, time_now)
            
            return fig_3d, orbit_list_updated, cam_mem, sat_ids

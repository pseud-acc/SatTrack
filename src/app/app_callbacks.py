#!/usr/bin/env python

"""

This module defines dash app callbacks used in the SatTrack app.

Example:

        $ python app_callbacks.py

Function:
    get_callbacks: wrapper function for callbacks
    update_3dviz: callback function for interactive 3d satellite visualisation
    update_2dviz: callback function for interactive 2d satellite visualisation
    update_tbl: callback function for table of satellites
    update_dropdown: callback function for satellite name and satcat number dynamic filter dropdown options

Todo:
    * 

"""

# 3rd party packages

import pandas as pd
import numpy as np

import time # Packages to compute satellite position
from dateutil import parser
from datetime import datetime, timedelta

from sgp4.api import Satrec, SatrecArray
from sgp4.api import SGP4_ERRORS
from sgp4.api import jday

import plotly.express as px # Packgaes to generate interactivity
import plotly.graph_objects as go
import dash_vtk
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import Dash, callback_context

# internal packages

from celestial_geometry_funs import compute_satloc, lla_to_xyz, sphere 
from app_settings import *
from initialise_app import (filter_df, orbit_path, satellite_3d_hover, satellite_2d_hover)

# Callback wrapper function
def get_callbacks(app,
                  df_in,
                  input_filter_in,
                  surf_3d_in,
                  fig3d_0_in,
                  layout_3d_in,
                  layout_2d_in,
                  tbl_col_map_in
                 ):
    ''' 
    Wrapper function that defines callbacks using app instantiation.

    @param app: (dash app object) instantiated app object

    @return:    
    '''
    
    # >>> Define Callbacks <<<    
    
    '''
    ------------------------
    3d visualisation 
    -------------------------
    Interactive Inputs: Filter dropdowns, Launch year slider, plot clicks, update time button, interval-timer
    Outputs: 3d Satellite scatter plot, 3d orbit line plot, camera view
    '''
    @app.callback(
            [
            Output('3d-earth-satellite-plot', 'figure'),
            Output('3d-orbit-memory', 'data'),
            Output('camera-memory',"data")
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
            Input("3d-earth-satellite-plot", "clickData"),
            Input('3d-orbit-memory', 'data'),
            Input("sat-viz-tabs","value"),
            Input("time-update-btn","n_clicks"),
            Input("clear-orbits-btn","n_clicks"),
            Input('3d-viz-interval-component', "n_intervals") 
        ],
            State('camera-memory',"data"),
            State('3d-earth-satellite-plot','relayoutData')
    )

    def update_3dviz(status, orbit, satname, satcatid,
                     owner, launchvehicle,
                     purpose, year, clickData, orbit_list, tab, 
                     update_time_btn, clear_orbits_btn,
                     cam_mem, cam_scene, time_intverval):

        if tab == "3d-viz":
            ctx = callback_context
            input_type = ctx.triggered[0]['prop_id'].split('.')[1] 
            input_name = ctx.triggered[0]['prop_id'].split('.')[0] 

            orbit_list_updated = orbit_list

            # Check for input updates - filter change or valid click (i.e. Satellite marker)
            if input_name == "clear-orbits-btn":
                orbit_list_updated = []

            if input_type == "clickData":
                if not clickData:
                    raise PreventUpdate
                elif clickData["points"][0]["curveNumber"] != 1:
                    raise PreventUpdate

            dff, time_now = filter_df(df_in, input_filter_in,
                 status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)

            # Do not update if existing 3d orbit is clicked
            if input_type == "clickData":
                if clickData["points"][0]["curveNumber"] == 1:
                    orbit_id = dff.iloc[[clickData["points"][0]["pointNumber"]]]["SatCatId"].values[0]
                    if orbit_id in orbit_list_updated:
                        raise PreventUpdate

            # 3D Visualisation Output
            scatter_3d = go.Scatter3d(x = dff["xp"].astype(np.float32), y = dff["yp"].astype(np.float32), z = dff["zp"].astype(np.float32),
                                   text = dff["ObjectName"], mode = "markers", showlegend = False,
                                   hoverlabel=dict(namelength=0), hoverinfo="text", hovertext=satellite_3d_hover(dff)[0],              
                                   marker = dict(color = np.where(dff["Status"]=="Active",1,0), cmin=0, cmax=1,
                                                 colorscale = colorscale_marker, opacity = 0.85, size = 2.5,
                                                 line=dict(color=np.where(dff["Status"]=="Active",1,0),
                                                   colorscale = colorscale_marker, width=0.01,
                                                  cmin=0, cmax=1))
                                        )

            fig_3d = go.Figure(data=[surf_3d_in,scatter_3d], layout=layout_3d_in)

            fig_3d.add_annotation(dict(font=dict(color=colours["atext"],size=12),
                               x=0.005, y=0.99, showarrow=False,
                               text=
                               '<i>Satellite position as at: ' + 
                               time_now.strftime("%H:%M:%S, %d/%m/%Y") + '</i> <br>' +
                               '<i>Number of active/inactive satellites shown: ' + 
                                "/".join([str(sum(dff.Status == "Active")),str(sum(dff.Status == "Inactive"))]) + 
                                ' (' + str(dff.shape[0]) + ' in total)' + '</i>',
                               textangle=0, xanchor='left',align='left',
                               xref="paper", yref="paper"))   
            fig_3d.add_annotation(dict(font=dict(color=colours["atext"],size=12),
                               x=0.67, y=0.02, showarrow=False,
                               text='Click satellite to show 3D orbital path',
                               textangle=0, xanchor='left',align='left',
                               xref="paper", yref="paper"))     

            try:
                cam_scene["scene.camera"]
            except:
                try:
                    cam_mem["scene.camera"]
                except:
                    fig_3d.update_layout(scene_camera = fig3d_0_in["layout"]["scene"]["camera"])
                else:
                    fig_3d.update_layout(scene_camera = cam_mem["scene.camera"])
            else:
                fig_3d.update_layout(scene_camera = cam_scene["scene.camera"])
                cam_mem = cam_scene["scene.camera"]


            # 3D Orbital Path - click-based
            if input_type == "clickData":
                if clickData["points"][0]["curveNumber"] == 1:
                    orbit_list_updated.append(dff.iloc[[clickData["points"][0]["pointNumber"]]]["SatCatId"].values[0])
                    orbit_list_updated = list(set(orbit_list_updated))
            if len(orbit_list_updated) > 0:
                for orbit_id in orbit_list_updated:
                    if orbit_id in dff["SatCatId"].values:
                        d3d = orbit_path(dff[dff["SatCatId"]==orbit_id],
                                         720, time_now, True)
                        fig_3d.add_scatter3d(x = d3d["xp"], y = d3d["yp"], z = d3d["zp"],
                            line = dict(color = np.where(d3d["Status"]=="Active",1,0), cmin=0, cmax=1,
                                        colorscale = colorscale_markerpath, width = 5),
                            mode = "lines", showlegend = False,
                            hoverlabel=dict(namelength=0), hoverinfo="text",
                            hovertext='<b>Satellite Name</b>: ' + d3d["ObjectName"]) 
                        fig_3d.add_scatter3d( x=[d3d["xp"][0]], y=[d3d["yp"][0]],  z=[d3d["zp"][0]],
                                marker = dict(color = np.where(d3d["Status"]=="Active",1,0), 
                                              colorscale = colorscale_markerpath,
                                              cmin=0, cmax=1,opacity = 0.65, size = 8),
                                mode = "markers", showlegend = False,
                                hoverlabel=dict(namelength=0),  hoverinfo="text",    
                                hovertext=satellite_3d_hover(d3d.iloc[[0]])[0]
                                            )                
        else:
            raise PreventUpdate

        return fig_3d, orbit_list_updated, cam_mem


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
            Input("sat-viz-tabs","value"),
            Input("time-update-btn","n_clicks"),
            Input('2d-viz-interval-component', "n_intervals")       
        ]
    )

    def update_2dviz(status, orbit, satname, satcatid,
                     owner, launchvehicle,
                     purpose, year, tab, update_time_btn, time_intverval):

        if tab == "2d-viz":         
            dff, time_now = filter_df(df_in, input_filter_in,
                 status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)

            #2D Visualisation
            if (satname != None or satcatid != None) & dff.shape[0] == 1: 
                d2d = orbit_path(dff, 3600, time_now, False)

                scatter_2d = go.Scattermapbox(lat=d2d["lat"], lon=d2d["lon"],
                    marker = dict(color = colours["marker1"], opacity = 0.1, size = 10),
                    mode = "markers", showlegend = False,
                    hoverlabel=dict(namelength=0), hoverinfo="text",    
                    hovertext=satellite_2d_hover(d2d)[0]
                ) 
                scatter_2d1 = go.Scattermapbox(lat=[d2d["lat"][0]], lon=[d2d["lon"][0]],
                        marker = dict(color = colours["marker2"], opacity = 0.6, size = 20),
                        mode = "markers", showlegend = False,
                        hoverlabel=dict(namelength=0), hoverinfo="text",    
                        hovertext= '<b>Current Position</b>' + '<br>' + satellite_2d_hover(d2d.iloc[[0]])[0]
                    )

            else:
                scatter_2d = go.Scattermapbox(lat=[0], lon=[0],
                    marker_opacity = 0, mode = "markers", showlegend = False,
                    hoverinfo='none', hoverlabel=dict(namelength=0)
                )        
                scatter_2d1 = scatter_2d

            fig_2d = go.Figure(data=[scatter_2d,scatter_2d1], layout=layout_2d_in)         

            # Table output
            dff["lat"] = round(dff["lat"],2); dff["lon"] = round(dff["lon"],2); 
            dff["alt"] = round(dff["alt"]).astype(int)
            dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")
        else:
            raise PreventUpdate

        return fig_2d

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
            Input("sat-viz-tabs","value"),
            Input("time-update-btn","n_clicks")
        ]
    )


    def update_tbl(status, orbit, satname, satcatid,
                     owner, launchvehicle,
                     purpose, year, tab, update_time_btn):

        if tab == "tbl-viz":   
            dff, time_now = filter_df(df_in, input_filter_in,
                 status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)

            # Table output
            dff["lat"] = round(dff["lat"],2); dff["lon"] = round(dff["lon"],2); 
            dff["alt"] = round(dff["alt"]).astype(int)
            dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")
        else:
            raise PreventUpdate

        return dff[tbl_col_map_in].sort_values(by=["ObjectName"]).rename(columns=tbl_col_map_in).to_dict("records")

   
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
            Output('satcatid-filter-dropdown', 'options')
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
        dff, _ = filter_df(df_in, input_filter_in,
                 status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)
        return list(np.sort(dff.ObjectName.unique())), list(np.sort(dff.SatCatId.unique()).astype(str))

#!/usr/bin/env python

"""

This module runs the SatTrackApp.

Example:

        $ python app.py

Attributes:

Todo:
    * Add update button to app
    * Add click event for 3d visualisation - generates 3d orbital path
    * Auto-update functionality for visualisations - every 20-30 seconds.

"""

import sys
import os
sys.path.append("./src/app/")

# 3rd party packages

import pandas as pd
import numpy as np
import json

import gunicorn # To run app on Heroku
from whitenoise import WhiteNoise

import time # Packages to compute satellite position
from dateutil import parser
from datetime import datetime, timedelta

from sgp4.api import Satrec, SatrecArray
from sgp4.api import SGP4_ERRORS
from sgp4.api import jday

import plotly.express as px # Packgaes to generate interactivity
import plotly.graph_objects as go
from dash import dcc
from dash import html
import dash_vtk
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import Dash, callback_context
import dash_bootstrap_components as dbc
from dash import Dash, dash_table

# internal packages

from celestial_geometry_funs import compute_satloc, lla_to_xyz, sphere 
from app_settings import *
from initialise_app import (import_data, filter_setup, initialise_2d, initialise_3d, filter_df,
                            orbit_path, satellite_3d_hover, satellite_2d_hover)


# //////////////////////////////////////////////////////////
## Dash App
# //////////////////////////////////////////////////////////

# Instantiate  App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
#server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

## --- Setup ----

# Import Data
"""
    Dynamic Satellite catalogue data - contains TLEs
"""
satcat_loc = "https://raw.githubusercontent.com/pseud-acc/SatTrack/main/dat/clean/satcat_tle.csv"

"""
    Greyscale Earth Map
"""
img_loc = "./static/gray_scale_earth_2048_1024.jpg"
resolution = 8
df, img, radius_earth = import_data(satcat_loc, img_loc, resolution)

# Initialise Filter 
options, input_filter, tbl_col_map = filter_setup(df)

# Initilise Visualisations
surf_3d, layout_3d, fig3d_0 = initialise_3d(df, img)
scatter_2d, layout_2d, fig2d_0  = initialise_2d()

## --- Define Dash layout ----

def create_dash_layout(app):

    # Set browser tab title
    app.title = "SatTrack"     
    
    # Main App Layout
    app.layout = html.Div([
        # Header
            html.H1(children="SatTrack", style = {'color': colours["ttext"]}),
            html.Div(children=
                     [html.H6('''
                     An Open Source Real-time Satellite Tracking App
                     ''', style = {'color': colours["ttext"], "display": "inline-block"}),
                      html.H6(children="Developed by Francis Nwobu", 
                              style = {"display": "inline-block", 'color': colours["ttext"], "float": "right"})
                     ], style={"display": "inline-block", "width":"100%"}),
    # Body - Main viz/sidebar
        html.Div([   
                # Sidebars
                html.Div([
                    # Checklist filters
                    html.P('Status', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": -5}),
                    dcc.Checklist(["Active","Inactive"],            #Operational Status
                                 ["Active"],
                                 id="status-filter-checkbox",
                                 inline=True,
                                  inputStyle={"margin-right": "2px", "margin-left": "6px"}
                                 ),
                    html.P('Orbit', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": -5}),
                    dcc.Checklist(options["orbit"],            #Orbital Class
                                  ["LEO"],
                                 id="orbit-filter-checkbox",
                                 inline=True,
                                  inputStyle={"margin-right": "2px", "margin-left": "6px"}
                                 ),
                    # Dropdown lists
                    html.P('Satellite Name', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": 0}),
                    dcc.Dropdown(options["satname"] ,            #Satellite Name
                              None,
                              id="satname-filter-dropdown",
                                 style ={'backgroundColor': colours["dropdownbox"],
                                         'font-size': fontsize["dropdown"]}),
                    html.P('SATCAT Number', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": 0}),
                    dcc.Dropdown(options["satcatid"] ,            #SATCAT Number
                              None,
                              id="satcatid-filter-dropdown",
                                 style ={'backgroundColor': colours["dropdownbox"],
                                         'font-size': fontsize["dropdown"]}),                
                    html.P('Owner', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": 0}),
                    dcc.Dropdown(options["owner"] ,            #Owner
                              [],
                              id="owner-filter-multi-dropdown",
                              multi=True,
                                 style ={'backgroundColor': colours["dropdownbox"],
                                         'font-size': fontsize["dropdown"]}),
                    html.P('Launch Vehicle', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": 0}),
                    dcc.Dropdown(options["launchvehicle"],            #Launch Vehicle Class
                                 [],
                                 id="launchvehicle-filter-multi-dropdown",
                                 multi=True,
                                 style ={'backgroundColor': colours["dropdownbox"],
                                         'font-size': fontsize["dropdown"]}),
                    html.P('Purpose', className = 'fix_label', 
                           style = {'color': colours["btext"],'font-weight': 'bold',
                                    "marginTop": 5,"marginBottom": 0}),
                    dcc.Dropdown(options["purpose"],            #Purpose
                                 [],
                                 id="purpose-filter-multi-dropdown",
                                 multi=True,
                                 style ={'backgroundColor': colours["dropdownbox"],
                                         'font-size': fontsize["dropdown"]}),
                    html.Div([
                         html.Button('Update Time', id='time-update-btn', n_clicks=0),
                         html.Button('Clear 3D Orbits', id='clear-orbits-btn', n_clicks=0,
                                    style = {"display": "inline-block","float": "right"})],
                    style={"marginTop": 20})
                ], style={"width": "25%", "display": "inline-block"}
                ),
                # Satellite viz
                html.Div([
                    dcc.Store(id='3d-orbit-memory', data=[]),
                    dcc.Store(id='camera-memory', data=fig3d_0["layout"]["scene"]["camera"]),
                    dcc.Tabs(
                        id="sat-viz-tabs",
                        value="3d-viz",
                        children=[
                            # 3d viz
                            dcc.Tab(label="3D Visualisation", value="3d-viz", children=[
                                dcc.Graph(id="3d-earth-satellite-plot",
                                         figure=fig3d_0)
                            ], style=tab_style, selected_style=tab_selected_style),
                            # Table viz
                             dcc.Tab(label="List of Satellites", value="tbl-viz", children=[
                                dash_table.DataTable(
                                    id="satellite-list",
                                    data=pd.DataFrame(columns=tbl_col_map.values()).to_dict("records"),
                                     virtualization=True,
                                     fixed_rows={'headers': True},
    #                                 filter_action="native"#,
                                     sort_action="native",
                                     sort_mode="multi",                                
                                     style_cell={'minWidth': 95, 'width': 95, 'maxWidth': 95, 
                                                 'textAlign':'center','backgroundColor':"black", 'color':colours["btext"]},
                                     style_table={'height': 400, 'overflowX':'auto'},  # default is 500
                                     style_data={'whiteSpace':'normal', 'height':'auto', 'lineHeight':'15px',
                                                 'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
                                                'border': '1px solid grey'},
                                     style_header={'backgroundColor': 'black','color': colours["btext"],
                                     'fontWeight': 'bold','border': '1px solid grey'},
                                      export_format="csv",
                                )
                             ], style=tab_style, selected_style=tab_selected_style),                             
                            # 2d viz - satellite tracker
                            dcc.Tab(label="2D Satellite Tracker", value="2d-viz",children=[
                                dcc.Graph(id="2d-earth-satellite-plot",
                                          figure=fig2d_0)
                            ], style=tab_style, selected_style=tab_selected_style)                       
                        ], style = tabs_styles
                    )

                ], style={"width": "70%", "float": "right", "display": "inline-block"}
                )

          ]),    
        # Slider filter
          html.Div([
              html.P('Launch Year', className = 'fix_label',
                     style = {'color': colours["btext"],'font-weight': 'bold',
                              "marginTop": 5,"marginBottom": 0}),
              dcc.RangeSlider(1955, 2025, 1,       #Launch Year
                              value=options["launchyear"],
                              marks={str(year): {'label': str(year), 'style':{'font-size': fontsize["dropdown"]}} for year in range(1955,2030,5)},
                              id="launchyear-filter-slider",
                              tooltip={"placement": "bottom", "always_visible": True})
          ],
            style={"width": "95%", "display": "inline-block"}
          )
        ], style={'width': '100%', 'padding': '20px 20px 20px 20px'})
    
    return app

create_dash_layout(app);

## --- Callback functionality - interactivity ----

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
        Input("clear-orbits-btn","n_clicks") 
    ],
        State('camera-memory',"data"),
        State('3d-earth-satellite-plot','relayoutData')
)

def update_3dviz(status, orbit, satname, satcatid,
                 owner, launchvehicle,
                 purpose, year, clickData, orbit_list, tab, 
                 update_time_btn, clear_orbits_btn,
                 cam_mem, cam_scene):
    
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
        
        dff, time_now = filter_df(df, input_filter,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)
        
        # Do not update if existing 3d orbit is clicked
        if input_type == "clickData":
            if clickData["points"][0]["curveNumber"] == 1:
                orbit_id = dff.iloc[[clickData["points"][0]["pointNumber"]]]["SatCatId"].values[0]
                if orbit_id in orbit_list_updated:
                    raise PreventUpdate
                    
        # 3D Visualisation Output
        scatter_3d = go.Scatter3d(x = dff["xp"], y = dff["yp"], z = dff["zp"], text = dff["ObjectName"],
                               mode = "markers", showlegend = False,
                               hoverlabel=dict(namelength=0), hoverinfo="text", hovertext=satellite_3d_hover(dff)[0],              
                               marker = dict(color = np.where(dff["Status"]=="Active",1,0), cmin=0, cmax=1,
                                             colorscale = colorscale_marker, opacity = 0.85, size = 2,
                                             line=dict(color=np.where(dff["Status"]=="Active",1,0),
                                               colorscale = colorscale_marker, width=0.01,
                                              cmin=0, cmax=1))
                                    )

        fig_3d = go.Figure(data=[surf_3d,scatter_3d], layout=layout_3d)

        fig_3d.add_annotation(dict(font=dict(color=colours["atext"],size=12),
                           x=0.005, y=0.99, showarrow=False,
                           text=
                           '<i>Satellite position as at: ' + 
                           time_now.strftime("%H:%M:%S, %d/%m/%Y") + '</i> <br>' +
                           '<i>Number of active/inactive satellites shown: ' + 
                            "/".join([str(sum(dff.Status == "Active")),str(sum(dff.Status == "Inactive"))]) + '</i>',
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
                fig_3d.update_layout(scene_camera = fig3d_0["layout"]["scene"]["camera"])
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
                                     360, time_now, True)
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
        Input("time-update-btn","n_clicks")       
    ]
)

def update_2dviz(status, orbit, satname, satcatid,
                 owner, launchvehicle,
                 purpose, year, tab, update_time_btn):
    
    if tab == "2d-viz":         
        dff, time_now = filter_df(df, input_filter,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)

        #2D Visualisation
        if (satname != None or satcatid != None) & dff.shape[0] == 1: 
            d2d = orbit_path(dff, 1800, time_now, False)

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

        fig_2d = go.Figure(data=[scatter_2d,scatter_2d1], layout=layout_2d)         

        # Table output
        dff["lat"] = round(dff["lat"],2); dff["lon"] = round(dff["lon"],2); 
        dff["alt"] = round(dff["alt"]).astype(int)
        dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")
    else:
        raise PreventUpdate
    
    return fig_2d

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

def update_graph(status, orbit, satname, satcatid,
                 owner, launchvehicle,
                 purpose, year, tab, update_time_btn):

    if tab == "tbl-viz":   
        dff, time_now = filter_df(df, input_filter,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)

        # Table output
        dff["lat"] = round(dff["lat"],2); dff["lon"] = round(dff["lon"],2); 
        dff["alt"] = round(dff["alt"]).astype(int)
        dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")
    else:
        raise PreventUpdate
        
    return dff[tbl_col_map].sort_values(by=["ObjectName"]).rename(columns=tbl_col_map).to_dict("records")

## --- Run App ----

if __name__ == "__main__": app.run_server(debug=False, host='0.0.0.0', port=8050)

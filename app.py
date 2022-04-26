#!/usr/bin/env python

"""

This module runs the SatTrackApp.

Example:

        $ python sattrackapp.py

Attributes:

Todo:
    * Add update button to app
    * Add click event for 3d visualisation - generates 3d orbital path
    * Auto-update functionality for visualisations - every 20-30 seconds.

"""

import sys
import os
sys.path.append("./src/")

import pandas as pd
import numpy as np

# Packages to compute satellite position
import time
from dateutil import parser
from datetime import datetime, timedelta

from sgp4.api import Satrec, SatrecArray
from sgp4.api import SGP4_ERRORS
from sgp4.api import jday

from celestial_geometry_funs import compute_satloc, lla_to_xyz, sphere # internal packages

# Packgaes to generate 3d interactive plot
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash import Dash
import dash_bootstrap_components as dbc
from dash import Dash, dash_table

from PIL import Image

# //////////////////////////////////////////////////////////
## APP SETTINGS
# //////////////////////////////////////////////////////////

## Colours - text, tabs, plots
colours = {
    "btext" : "#dae0e3", #grey - app button text
    "ttext" : "#dae9f2", #greyish-blue - app title text
    "atext" : "#ffffff", #white - 3d plot annotation text
    "marker" : "#e00000", #red - marker for Satellites    
    "marker2" : "#49fcf3", #cyan - marker for current satellite position
    "markeredge" : "#b84949", #greyish-red - marker edge for Satellites
    "tab": "#7c919c" #greyish-blue - tab background
}

## Colour scale to convert 2d greyscale of Earth to coloured texture
colorscale =[[0.0, 'rgb(30, 59, 117)'],

             [0.1, 'rgb(46, 68, 21)'],
             [0.2, 'rgb(74, 96, 28)'],
             [0.3, 'rgb(115,141,90)'],
             [0.4, 'rgb(122, 126, 75)'],

             [0.6, 'rgb(122, 126, 75)'],
             [0.7, 'rgb(141,115,96)'],
             [0.8, 'rgb(223, 197, 170)'],
             [0.9, 'rgb(237,214,183)'],

             [1.0, 'rgb(255, 255, 255)']]

## Tab Styles
tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '2px solid ' + colours["ttext"],
    'padding': '6px',
    'fontWeight': 'bold'
}
tab_selected_style = {
    'borderTop': '1px solid ' + colours["ttext"],
    'borderBottom': '1px solid ' + colours["ttext"],
    'backgroundColor': colours["tab"],
    'color': colours["ttext"],
    'padding': '6px'
}

# Earth Radius
radius_earth = 6378.137 

# //////////////////////////////////////////////////////////
## IMPORT DATA
# //////////////////////////////////////////////////////////

## Satellite catalogue data - contains TLEs
filename = "./dat/clean/satcat_tle.csv"
satcat = pd.read_csv(filename)

print("Satcat imported", satcat.shape)

## Greyscale Earth Map
filename = "./res/gray_scale_earth_2048_1024.jpg"
img = np.asarray(Image.open(filename))
img = img.T

print("Earth Map imported", img.shape)

# Compress image
img_compr = img[0:-1:2,0:-1:2]

# //////////////////////////////////////////////////////////
## Dash App
# //////////////////////////////////////////////////////////

## Data Setup
df = satcat.copy()

# Create filter options
orbit_options = np.sort(df.OrbitClass.unique())

owner_options = list(np.sort(df.Owner.unique()))

launchvehicle_options = list(np.sort(df.LaunchVehicleClass.unique()))

purpose_options = sorted(list(set(sum([a.split("/") for a in df.Purpose.unique()], []))))

satname_options = list(np.sort(df.ObjectName.unique()))

satcatid_options = list(np.sort(df.SatCatId.unique()).astype(str))

tbl_col_map = {"ObjectName":"Satellite Name", "SatCatId": "SATCAT Number", "Status":"Status",
          "OrbitClass":"Orbit", "LaunchYear": "Year of Launch", "Owner":"Owner",
          "lat":"Latitude", "lon":"Longitude", "alt":"Altitude (km)", "Datetime":"Datetime (UTC)"}

#Input filter dictionary
temp_cols = ["SatCatId","ObjectName","LaunchSiteCountry","Owner","UseType","LaunchVehicleClass"] 

input_filter = dict()
for col in temp_cols:
    input_filter[col] = satcat[col].unique()
input_filter["OrbitClass"] = np.array(["LEO","MEO","GEO","HEO"])
input_filter["LaunchYear"] = np.array(range(satcat["LaunchYear"].min(),satcat["LaunchYear"].max()+1))
input_filter["Purpose"] = purpose_options

print(input_filter)

## Default Figure - 3d Earth

# 3D Visualisation Output
x,y,z = sphere(radius_earth,img_compr)
surf_3d = go.Surface(x=x, y=y, z=z,
                  surfacecolor=img_compr,
                  colorscale=colorscale,
                  showscale=False,
                  hoverinfo="none")            

R1 = 40000 #axis range
axis_range = [-R1-radius_earth, radius_earth+R1]
layout_3d = go.Layout(scene=dict(aspectratio=dict(x=1, y=1, z=1),
                    yaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                    xaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                    zaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range)
                             ),
                  showlegend=False,
                  paper_bgcolor="black",
                  margin=dict(l=0, r=0, t=0, b=0))
fig3d_0 = go.Figure(data=[surf_3d], layout=layout_3d)

# 2D Visualisation Output
scatter_2d = go.Scattermapbox(
    lat=[0], lon=[0],
    marker_opacity = 0,
    mode = "markers",
    showlegend = False,
    hoverinfo='none',
    hoverlabel=dict(namelength=0)    
)

layout_2d = go.Layout(    
    width=500,
    height=500,
    margin={"r":0,"t":0,"l":0,"b":0},
    mapbox=dict(
        style="white-bg",
        center_lat = 0,
        center_lon = 0,        
        zoom=0,
        bearing=0,
        pitch=0,  
        layers=[
            {
                "below": 'traces',
                "sourcetype": "raster",
                "sourceattribution": "United States Geological Survey",
                "source": [
                    "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                ]
        }
      ])
)

fig2d_0 = go.Figure(data=[scatter_2d], layout=layout_2d)

## Initialise App
external_stylesheets = [dbc.themes.CYBORG]
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

## App Layout
app.layout = html.Div([
        html.H1(children="SatTrack", style = {'color': colours["ttext"]}),
        html.Div(children=
                 [html.H6('''
                 An Open Source Real-time Satellite Tracking App
                 ''', style = {'color': colours["ttext"], "display": "inline-block"}),
                  html.H6(children="Developed by Francis Nwobu", 
                          style = {"display": "inline-block", 'color': colours["ttext"], "float": "right"})
                 ], style={"display": "inline-block", "width":"100%"}),
    html.Div([   
        
            html.Div([
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
                dcc.Checklist(orbit_options,            #Orbital Class
                              ["LEO"],
                             id="orbit-filter-checkbox",
                             inline=True,
                              inputStyle={"margin-right": "2px", "margin-left": "6px"}
                             ),
                html.P('Satellite Name', className = 'fix_label', 
                       style = {'color': colours["btext"],'font-weight': 'bold',
                                "marginTop": 5,"marginBottom": 0}),
                dcc.Dropdown(satname_options ,            #Satellite Name
                          None,
                          id="satname-filter-dropdown"),
                html.P('SATCAT Number', className = 'fix_label', 
                       style = {'color': colours["btext"],'font-weight': 'bold',
                                "marginTop": 5,"marginBottom": 0}),
                dcc.Dropdown(satcatid_options ,            #SATCAT Number
                          None,
                          id="satcatid-filter-dropdown"),                
                html.P('Owner', className = 'fix_label', 
                       style = {'color': colours["btext"],'font-weight': 'bold',
                                "marginTop": 5,"marginBottom": 0}),
                dcc.Dropdown(owner_options ,            #Owner
                          [],
                          id="owner-filter-multi-dropdown",
                          multi=True),
                html.P('Launch Vehicle', className = 'fix_label', 
                       style = {'color': colours["btext"],'font-weight': 'bold',
                                "marginTop": 5,"marginBottom": 0}),
                dcc.Dropdown(launchvehicle_options,            #Launch Vehicle Class
                          [],
                          id="launchvehicle-filter-multi-dropdown",
                          multi=True),
                html.P('Purpose', className = 'fix_label', 
                       style = {'color': colours["btext"],'font-weight': 'bold',
                                "marginTop": 5,"marginBottom": 0}),
                dcc.Dropdown(purpose_options,            #Purpose
                           [],
                           id="purpose-filter-multi-dropdown",
                           multi=True)
            ], style={"width": "25%", "display": "inline-block"}
            ),
        
            html.Div([
                dcc.Tabs(
                    id="sat-viz-tabs",
                    value="3d-viz",
                    children=[
                        dcc.Tab(label="3D Visualisation", value="3d-viz", children=[
                            dcc.Graph(id="3d-earth-satellite-plot",
                                     figure=fig3d_0)
                        ], style=tab_style, selected_style=tab_selected_style),
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
                        
                        dcc.Tab(label="2D Satellite Tracker", value="2d-viz",children=[
                            dcc.Graph(id="2d-earth-satellite-plot",
                                      figure=fig2d_0)
                        ], style=tab_style, selected_style=tab_selected_style)                       
                    ], style = tabs_styles
                )
                      
            ], style={"width": "70%", "float": "right", "display": "inline-block"}
            )
            
      ]),    
    
      html.Div([
          html.P('Launch Year', className = 'fix_label',
                 style = {'color': colours["btext"],'font-weight': 'bold',
                          "marginTop": 5,"marginBottom": 0}),
          dcc.RangeSlider(1955, 2025, 1,       #Launch Year
                          value=[df.LaunchYear.min(),df.LaunchYear.max()],
                          marks={str(year): str(year) for year in range(1955,2030,5)},
                          id="launchyear-filter-slider")
      ],
        style={"width": "95%", "display": "inline-block"}
      )
    ], style={'width': '100%', 'padding': '20px 20px 20px 20px'})

## Update Figure Function
@app.callback(
    [
        Output('3d-earth-satellite-plot', 'figure'),
        Output('2d-earth-satellite-plot', 'figure'),
        Output('satellite-list', 'data')
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

def update_graph(status, orbit, satname, satcatid,
                 owner, launchvehicle,
                 purpose, year):
     
    input_filter_update = input_filter.copy()
    input_filter_update["Status"] =  status      
    input_filter_update["OrbitClass"] = orbit
    if satname is not None:
        input_filter_update["ObjectName"] = [satname]
    if satcatid is not None:
        input_filter_update["SatCatId"] = [int(satcatid)]        
    if len(owner) != 0:
        input_filter_update["Owner"] = owner         
    if len(launchvehicle) != 0: 
        input_filter_update["LaunchVehicleClass"] = launchvehicle
    if len(purpose) != 0:    
        input_filter_update["Purpose"] = purpose
    input_filter_update["LaunchYear"] = list(range(year[0],year[1]+1))        


    
    dff = df.copy()
    for col,vals in input_filter_update.items():
        if col == "Purpose":
            indx = dff.Purpose.str.split("/").apply(lambda x: True if len(set(x).intersection(set(vals))) > 0 else False)     
            if len(indx) > 0: dff = dff[indx]
        else:
            dff = dff[dff[col].isin(vals)]    
                
    time_now = datetime.utcnow()
    
    dff[["x","y","z","lat","lon","alt"]] = compute_satloc(dff[["TLE1","TLE2"]].values, time_now, radius_earth)
    
    dff = dff.dropna()
    
    dff["xp"], dff["yp"], dff["zp"] = lla_to_xyz(dff.lat,dff.lon,dff.alt,radius_earth)
        
   
    # 3D Visualisation Output
    scatter_3d = go.Scatter3d(x = dff["xp"],
                           y = dff["yp"],
                           z = dff["zp"],
                           text = dff["ObjectName"],
                           mode = "markers",
                           showlegend = False,
                           hoverlabel=dict(namelength=0),
                           hoverinfo="text",
                           hovertext=
                           '<b>Satellite Name</b>: ' + dff["ObjectName"] + '<br>' +
                           '<b>SATCAT Number</b>: ' + dff["SatCatId"].astype(str) + '<br>' +
                           '<b>Status</b>: ' + dff["Status"] + '<br>' +
                           '<b>Orbit</b>: ' + dff["OrbitClass"] + '<br>' +
                           '<b>Launch Year</b>: ' + dff["LaunchYear"].astype(str) + '<br>' +
                           '<b>Owner</b>: ' + dff["Owner"] + '<br>' +
                           '<b>Lat, Lon, Alt</b>: (' + 
                           round(dff["lat"],2).astype(str) + '&deg;, ' + 
                           round(dff["lon"],2).astype(str) + '&deg;, ' +
                           round(dff["alt"]).astype(int).astype(str) + 'km' +
                           ')',              
                           marker = dict(color = colours["marker"],
                                         opacity = 0.5,
                                         size = 2.5,
                                         line=dict(color=colours["markeredge"], width=0.01)
                                        )
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
    
    #2D Visualisation
    if (satname != None or satcatid != None) & dff.shape[0] == 1: 
        time_lapse = []
        time_now = datetime.utcnow()
        orbit_dt = np.linspace(0,dff["OrbitalPeriod"].values[0],3600)
        for dt in orbit_dt:
            time_lapse = np.append(time_lapse,(time_now + timedelta(minutes=dt)).replace(microsecond=0))
        d2d = pd.DataFrame(compute_satloc(dff[["TLE1","TLE2"]].values[0], time_lapse, radius_earth), 
                           columns =["x","y","z","lat","lon","alt"])
        d2d["Datetime"] = time_lapse; 

        scatter_2d = go.Scattermapbox(
            lat=d2d["lat"], lon=d2d["lon"],
            marker = dict(color = colours["marker"],
                         opacity = 0.1,
                         size = 10
                        ),
            mode = "markers",
            showlegend = False,
            hoverlabel=dict(namelength=0),
            hoverinfo="text",    
            hovertext=
                '<b>Lat</b>: ' + round(d2d["lat"],2).astype(str) + '&deg;' + '<br>' +
                '<b>Lon</b>: ' + round(d2d["lon"],2).astype(str) + '&deg;' + '<br>' +
                '<b>Alt</b>: ' + round(d2d["alt"]).astype(int).astype(str) + 'km <br>' +  
                '<b>Datetime (UTC)</b>: ' + d2d["Datetime"].astype(str)
        ) 
        scatter_2d1 = go.Scattermapbox(
                lat=[d2d["lat"][0]], lon=[d2d["lon"][0]],
                marker = dict(color = colours["marker2"],
                             opacity = 0.6,
                             size = 20
                            ),
                mode = "markers",
                showlegend = False,
                hoverlabel=dict(namelength=0),
                hoverinfo="text",    
                hovertext=
                '<b>Current Position</b>' + '<br>' + '<br>' +
                '<b>Lat</b>: ' + str(round(d2d["lat"][0],2)) + '&deg;' + '<br>' +
                '<b>Lon</b>: ' + str(round(d2d["lon"][0],2)) + '&deg;' + '<br>' +
                '<b>Alt</b>: ' + str(int(round(d2d["alt"][0]))) + 'km <br>' +  
                '<b>Datetime (UTC)</b>: ' + str(d2d["Datetime"][0])
            )
    else:
        scatter_2d = go.Scattermapbox(
            lat=[0], lon=[0],
            marker_opacity = 0,
            mode = "markers",
            showlegend = False,
            hoverinfo='none',
            hoverlabel=dict(namelength=0)
        )        
        scatter_2d1 = scatter_2d
        
    fig_2d = go.Figure(data=[scatter_2d,scatter_2d1], layout=layout_2d)         
        
    
    # Table output
    dff["lat"] = round(dff["lat"],2); dff["lon"] = round(dff["lon"],2); 
    dff["alt"] = round(dff["alt"]).astype(int)
    dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")
    
    return fig_3d, fig_2d, dff[tbl_col_map].sort_values(by=["ObjectName"]).rename(columns=tbl_col_map).to_dict("records")

## Run App
app.run_server(port = 8090, dev_tools_ui=True, #debug=True,
              dev_tools_hot_reload =True, threaded=True)

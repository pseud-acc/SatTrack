#!/usr/bin/env python

"""

This module initialises app - imports required data and creates default figures.

Example:

        $ python intialise_data.py

Attributes:

Todo:
    * 

"""
# 3rd party packages

import pandas as pd
import numpy as np
from PIL import Image 

import plotly.express as px 
import plotly.graph_objects as go

# internal packages

from celestial_geometry_funs import sphere 
from app_settings import *

# Earth Radius
radius_earth = 6378.137 

def import_data(satcat_loc, img_loc):
    ''' 
    Import satellite data and earth map.

    @param satcat_loc: dynamic location of satellite data
    @param img_loc: static location of Earth map
    @return satcat:  dataframe of satellite data 
    @return img_compr:  compressed image array of Earth map
    @return tbl_col_map: dict of column name mapping for table export
    '''          
    ## Satellite catalogue data - contains TLEs
    satcat_loc = "https://raw.githubusercontent.com/pseud-acc/SatTrack/main/dat/clean/satcat_tle.csv"
    satcat = pd.read_csv(satcat_loc)

    print("Satellite catalgoue and TLEs successfully imported!")

    img = np.asarray(Image.open(img_loc))
    img = img.T

    print("Earth Map successfully imported!")

    # Compress image
    img_compr = img[0:-1:2,0:-1:2]

    return satcat, img_compr, radius_earth


def filter_setup(df):
    ''' 
    Initialise filter and table columns.

    @param df: (array) satellite catalogue array
    @return options:  dict of filter options for dropdown and checkbox
    @return input_filter:  dict of filter options for dataframe
    @return tbl_col_map: dict of column name mapping for table export
    '''             
    
    options = {}
    
    # Create dropdown filter options
    options["orbit"] = np.sort(df.OrbitClass.unique())

    options["owner"] = list(np.sort(df.Owner.unique()))

    options["launchvehicle"] = list(np.sort(df.LaunchVehicleClass.unique()))

    options["purpose"] = sorted(list(set(sum([a.split("/") for a in df.Purpose.unique()], []))))

    options["satname"] = list(np.sort(df.ObjectName.unique()))

    options["satcatid"] = list(np.sort(df.SatCatId.unique()).astype(str))
    
    options["launchyear"] = [df.LaunchYear.min(),df.LaunchYear.max()]

    #Input filter dictionary
    temp_cols = ["SatCatId","ObjectName","LaunchSiteCountry","Owner","UseType","LaunchVehicleClass"] 

    input_filter = dict()
    for col in temp_cols:
        input_filter[col] = df[col].unique()
    input_filter["OrbitClass"] = np.array(["LEO","MEO","GEO","HEO"])
    input_filter["LaunchYear"] = np.array(range(df["LaunchYear"].min(),df["LaunchYear"].max()+1))
    input_filter["Purpose"] = options["purpose"]

    tbl_col_map = {"ObjectName":"Satellite Name", "SatCatId": "SATCAT Number", "Status":"Status",
              "OrbitClass":"Orbit", "LaunchYear": "Year of Launch", "Owner":"Owner",
              "lat":"Latitude", "lon":"Longitude", "alt":"Altitude (km)", "Datetime":"Datetime (UTC)"}
    
    return options, input_filter, tbl_col_map


def initialise_3d(df, img):
    
    ''' 
    Initialise default 3d visualisation.

    @param df: (array) satellite catalogue array
    @return scatter_3d:  3d scatter graph object
    @return layout_3d:  graph layout object  
    @return fig_3d:  figure object      
    '''         
    
    x,y,z = sphere(radius_earth,img)
    surf_3d = go.Surface(x=x, y=y, z=z,
                      surfacecolor=img,
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
    fig_3d = go.Figure(data=[surf_3d], layout=layout_3d)
    
    return surf_3d, layout_3d, fig_3d

def initialise_2d():
    
    ''' 
    Initialise default 2d visualisation.

    @return scatter_2d:  2d scatter graph object
    @return layout_2d:  graph layout object  
    @return fig_2d:  figure object      
    '''           
    
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

    fig_2d = go.Figure(data=[scatter_2d], layout=layout_2d)    
    
    return scatter_2d, layout_2d, fig_2d
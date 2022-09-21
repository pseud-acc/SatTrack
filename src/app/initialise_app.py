#!/usr/bin/env python

"""

This module initialises app - imports required data, creates default figures and defines helper functions for plotting.

Example:

        $ python intialise_app.py

Attributes:

Todo:
    * 

"""
# 3rd party packages

import pandas as pd
import numpy as np
from PIL import Image 

from datetime import datetime, timedelta

import plotly.express as px 
import plotly.graph_objects as go

# internal packages

from celestial_geometry_funs import compute_satloc, lla_to_xyz, sphere 
from app_settings import *

# Earth Radius
radius_earth = 6378.137 

def import_data(satcat_loc, img_loc, res):
    ''' 
    Import satellite data and earth map.

    @param satcat_loc: dynamic location of satellite data
    @param img_loc: static location of Earth map
    @param res: integer - Earth map resolution in increments of 2^x for integer x
    @return satcat:  dataframe of satellite data 
    @return img_compr:  compressed image array of Earth map
    @return tbl_col_map: dict of column name mapping for table export
    '''          
    ## Satellite catalogue data - contains TLEs

    satcat = pd.read_csv(satcat_loc)

    print("Satellite catalgoue and TLEs successfully imported!")

    img = np.asarray(Image.open(img_loc))
    img = img.T

    print("Earth Map successfully imported!")

    # Compress image
    img_compr = img[0:-1:res,0:-1:res]

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

    R1 = 200000 #axis range
    axis_range = [-R1-radius_earth, radius_earth+R1]
    layout_3d = go.Layout(scene=dict(aspectratio=dict(x=1, y=1, z=1),
                        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        zaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        camera=dict(up=dict(x=0, y=0, z=1),
                                    center=dict(x=0, y=0, z=0),
                                    eye=dict(x=0.035, y=-0.2,z=0.12),
                                    projection=dict(type='perspective')
                                   )),
                      #uirevision='true',
                      showlegend=False,
                      paper_bgcolor="black",
                      margin=dict(l=0, r=0, t=0, b=0))
    fig_3d = go.Figure(data=[surf_3d], layout=layout_3d)
    
    return surf_3d, layout_3d, fig_3d

def initialise_3d_ls(df, img):
    
    ''' 
    Initialise default 3d visualisation in low memory mode

    @param df: (array) satellite catalogue array
    @return scatter_3d:  3d scatter graph object
    @return layout_3d:  graph layout object  
    @return fig_3d:  figure object      
    '''         
    
    x,y,z = sphere(radius_earth,img)
    surf_3d = go.Surface(x=x.astype(np.float32), y=y.astype(np.float32), z=z.astype(np.float32),
                      surfacecolor=img,
                      colorscale=colorscale,
                      showscale=False,
                      hoverinfo="none")            

    R1 = 200000 #axis range
    axis_range = [-R1-radius_earth, radius_earth+R1]
    layout_3d = go.Layout(scene=dict(aspectratio=dict(x=1, y=1, z=1),
                        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        zaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        camera=dict(up=dict(x=0, y=0, z=1),
                                    center=dict(x=0, y=0, z=0),
                                    eye=dict(x=0., y=-0.25,z=0.04),
                                    projection=dict(type='perspective')
                                   )),
                      #uirevision='true',
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

def filter_df(df_in, input_filter,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year):
    ''' 
    Create hover text for satellites in 3d visualisation.

    @param df_plot: (dataframe) data to plot
    @return: string array of descriptive text.
    '''     
    
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

    # If filter has been updated, filter and return new dataframe
    for col,vals in input_filter_update.items():
        if col == "Purpose":
            indx = df_in.Purpose.str.split("/").apply(lambda x: True if len(set(x).intersection(set(vals))) > 0 else False)     
            if len(indx) > 0: df_in = df_in[indx]
        else:
            df_in = df_in[df_in[col].isin(vals)]    
                
    time_now = datetime.utcnow()
    
    df_in[["x","y","z","lat","lon","alt"]] = compute_satloc(df_in[["TLE1","TLE2"]].values, time_now, radius_earth, False)
    
    df_in = df_in.dropna()
    
    df_in["xp"], df_in["yp"], df_in["zp"] = lla_to_xyz(df_in.lat,df_in.lon,df_in.alt,radius_earth)
    
    return df_in, time_now

def orbit_path(df_in, res, time_now, eci):
    ''' 
    Create hover text for satellites in 3d visualisation.

    @param df_plot: (dataframe) data to plot
    @return: string array of descriptive text.
    '''      
    orbit_dt = np.linspace(0,1.*float(df_in["OrbitalPeriod"].values[0]), res)
    time_lapse=[]
    for dt in orbit_dt:
        time_lapse = np.append(time_lapse,(time_now + timedelta(minutes=dt)).replace(microsecond=0))
    df_path = pd.DataFrame(compute_satloc(df_in[["TLE1","TLE2"]].astype(str).values[0], time_lapse, radius_earth, eci), 
                       columns =["x","y","z","lat","lon","alt"])
    df_path["xp"], df_path["yp"], df_path["zp"] = lla_to_xyz(df_path.lat,df_path.lon,df_path.alt,radius_earth)    
    for col in (df_path.columns).symmetric_difference(df_in.columns):
        df_path[col] = df_in[col].values[0]
    df_path["Datetime"] = time_lapse; 
    return df_path

def satellite_3d_hover(df_plot):
    ''' 
    Create hover text for satellites in 3d visualisation.

    @param df_plot: (dataframe) data to plot
    @return: string array of descriptive text.
    '''     
    return ['<b>Satellite Name</b>: ' + df_plot["ObjectName"] + '<br>' + '<b>SATCAT Number</b>: ' + 
            df_plot["SatCatId"].astype(str) + '<br>' +
            '<b>Status</b>: ' + df_plot["Status"] + '<br>' +
            '<b>Orbit</b>: ' + df_plot["OrbitClass"] + '<br>' +
            '<b>Launch Year</b>: ' + df_plot["LaunchYear"].astype(str) + '<br>' +
            '<b>Owner</b>: ' + df_plot["Owner"] + '<br>' +
            '<b>Lat, Lon, Alt</b>: (' + 
            round(df_plot["lat"],2).astype(str) + '&deg;, ' + 
            round(df_plot["lon"],2).astype(str) + '&deg;, ' +
            round(df_plot["alt"]).astype(int).astype(str) + 'km' +
            ')']

def satellite_3d_hover2(df_plot):
    ''' 
    Create hover text for satellites in 3d visualisation.

    @param df_plot: (dataframe) data to plot
    @return: string array of descriptive text.
    '''     
    return ['<b>Satellite Name</b>: ' + df_plot["ObjectName"] + '<br>' + '<b>SATCAT Number</b>: ' + 
            df_plot["SatCatId"].astype(str) + '<br>' +
            '<b>Status</b>: ' + df_plot["Status"] + '<br>' +
            '<b>Orbit</b>: ' + df_plot["OrbitClass"]]

def satellite_2d_hover(df_plot):
    ''' 
    Create hover text for satellites in 2d visualisation.

    @param df_plot: (dataframe) data to plot
    @return: string array of descriptive text.
    '''  
    
    return['<b>Lat</b>: ' + round(df_plot["lat"],2).astype(str) + '&deg;' + '<br>' +
           '<b>Lon</b>: ' + round(df_plot["lon"],2).astype(str) + '&deg;' + '<br>' +
           '<b>Alt</b>: ' + round(df_plot["alt"]).astype(int).astype(str) + 'km <br>' +  
           '<b>Datetime (UTC)</b>: ' + df_plot["Datetime"].astype(str)]
"""

This module defines functions to assist with generating app data

Example:

        $ python helper__app_data.py

Function:
    create_data_filters: Initialise filter and table columns
    filter_satellite_data: Filter dataframe based on user inputs
    generate_orbital_path: Calculate orbital path for satellite
Todo:
    *

"""

## Imports
# Standard libraries
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Internal modules
from app.helper.helper__satellite_position import (compute_satloc, lla_to_xyz)
from app.helper.helper__constants import _radius_earth__c

def create_data_filters(df):
    ''' 
    Initialise filter and table columns.

    @param df: (array) satellite catalogue array
    @return options:  dict of filter options for dropdown and checkbox
    @return init_filter: dict of initial filter values
    @return tbl_col_map: dict of column name mapping for table export
    '''             
    
    options = {}
    
    # Create dropdown filter options
    options["orbit"] = ["LEO","MEO","GEO","GSO","HEO"] #np.sort(df.OrbitClass.unique())

    options["owner"] = list(np.sort(df.Owner.unique()))

    options["launchvehicle"] = list(np.sort(df.LaunchVehicleClass.unique()))

    options["purpose"] = sorted(list(set(sum([a.split("/") for a in df.Purpose.unique()], []))))

    options["satname"] = list(np.sort(df.ObjectName.unique()))

    options["satcatid"] = list(np.sort(df.SatCatId.unique()).astype(str))
    
    options["launchyear"] = [df.LaunchYear.min(),df.LaunchYear.max()]

    #Input filter dictionary
    temp_cols = ["SatCatId","ObjectName","LaunchSiteCountry","Owner","UseType","LaunchVehicleClass"] 

    init_filter = dict()
    for col in temp_cols:
        init_filter[col] = df[col].unique()
    init_filter["OrbitClass"] = np.array(["LEO","MEO","GEO","GSO","HEO"])
    init_filter["LaunchYear"] = np.array(range(df["LaunchYear"].min(),df["LaunchYear"].max()+1))
    init_filter["Purpose"] = options["purpose"]
    
    return options, init_filter

def filter_satellite_data(df_in, input_filter,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year):
    ''' 
    Filter dataframe based on user inputs (pure function).

    @param df_in: (DataFrame) Input satellite catalogue dataframe
    @param input_filter: (dict) Current filter dictionary
    @param status: (list) List of status filters
    @param orbit: (list) List of orbit class filters
    @param satname: (str) Satellite name filter
    @param satcatid: (str) Satellite catalog ID filter
    @param owner: (list) List of owner filters
    @param launchvehicle: (list) List of launch vehicle class filters
    @param purpose: (list) List of purpose filters
    @param year: (list) Year range [min, max]
    @return: (DataFrame) Filtered dataframe
    '''     
    # Create updated filter dictionary
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
                
    # Compute satellite locations at current time
    time_now = datetime.utcnow()

    df_in[["x","y","z","lat","lon","alt"]] = compute_satloc(df_in[["TLE1","TLE2"]].values, time_now, _radius_earth__c, False)
    
    df_in = df_in.dropna()
    
    df_in["xp"], df_in["yp"], df_in["zp"] = lla_to_xyz(df_in.lat,df_in.lon,df_in.alt,_radius_earth__c)

    # Generate encoded satelite status for plotting
    sat_status_encoded = np.where(df_in["Status"] == "Active", 1, 0)
    
    return df_in, time_now, sat_status_encoded


def generate_orbital_path(df_in, res, time_now, eci):
    ''' 
    Calculate orbital path for satellite (pure function).

    @param df_in: (DataFrame) Dataframe with satellite data (single row expected)
    @param res: (int) Number of time steps to calculate (resolution)
    @param time_now: (datetime) Current timestamp
    @param eci: (bool) Whether to calculate ECI (3D) or geodetic (2D) coordinates
    @return: (DataFrame) Dataframe with orbital path coordinates
    '''      
    # Calculate delta times for orbit path
    orbit_dt = np.linspace(0,1.*float(df_in["OrbitalPeriod"].values[0]), res)

    # Generate time lapse array
    time_lapse=[]
    for dt in orbit_dt:
        time_lapse = np.append(time_lapse,(time_now + timedelta(minutes=dt)).replace(microsecond=0))
    df_path = pd.DataFrame(compute_satloc(df_in[["TLE1","TLE2"]].astype(str).values[0], time_lapse, _radius_earth__c, eci), 
                       columns =["x","y","z","lat","lon","alt"])
    df_path["xp"], df_path["yp"], df_path["zp"] = lla_to_xyz(df_path.lat,df_path.lon,df_path.alt,_radius_earth__c)    
    for col in np.setdiff1d(list(df_in.columns),list(df_path.columns)):
        df_path[col] = df_in[col].values[0]
    df_path["Datetime"] = time_lapse

    return df_path
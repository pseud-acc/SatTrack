"""

This module defines functions to assist with generating app data

Example:

        $ python helper__app_data.py

Function:
    create_data_filters: Sidebar options
    sidebar_filter_spec: The filter spec for the sidebar's values
    filter_satellite_data: Filter dataframe based on user inputs, through the filter spec
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
from app.helper.helper__satellite_position import (compute_satloc, lla_to_xyz, satrecs_for)
from app.helper.helper__constants import _radius_earth__c
from app.core import filter_spec

def create_data_filters(df):
    '''
    Sidebar options, built from the app CSV.

    @param df: (DataFrame) satellite catalogue (the app CSV)
    @return options: dict of filter options for the dropdowns, checkboxes and the launch-year slider
    '''
    options = {}
    options["orbit"] = ["LEO","MEO","GEO","GSO","HEO"]
    options["owner"] = list(np.sort(df.Owner.unique()))
    options["launchvehicle"] = list(np.sort(df.LaunchVehicleClass.unique()))
    options["purpose"] = sorted(list(set(sum([a.split("/") for a in df.Purpose.unique()], []))))
    options["satname"] = list(np.sort(df.ObjectName.unique()))
    options["satcatid"] = list(np.sort(df.SatCatId.unique()).astype(str))
    options["launchyear"] = [df.LaunchYear.min(),df.LaunchYear.max()]
    return options


# The sidebar shows "Unknown" where the objects dataset has no value (D-032): in a spec that is null.
UNKNOWN = "Unknown"


def _with_null(values):
    return [None if v == UNKNOWN else v for v in values]


def sidebar_filter_spec(status, orbit, satname, satcatid, owner, launchvehicle, purpose, year):
    '''
    The filter spec (D-031) for the sidebar's values, in the objects dataset's field names (D-030).

    Rules, unchanged from before the spec: status and orbit class are "any of" the ticked values; name and
    catalogue number are exact; owner, launch vehicle and purpose filter only when something is selected, and
    purpose matches any of an object's labels; launch year is an inclusive range. "Unknown" in a dropdown is a
    missing value. "Inactive" also covers objects with no status, as the app CSV always has (it fills a missing
    status with "Inactive").

    @return: (dict) the spec, or None when the values can select nothing (no status or no orbit class ticked)
    '''
    if not status or not orbit:
        return None
    status_values = list(status) + ([None] if "Inactive" in status else [])
    clauses = [
        {"field": "operational_status", "op": "in", "value": status_values},
        {"field": "orbit_class", "op": "in", "value": list(orbit)},
        {"field": "launch_year", "op": "between", "value": {"min": int(year[0]), "max": int(year[1])}},
    ]
    if satname is not None:
        clauses.append({"field": "object_name", "op": "is_missing", "value": True} if satname == UNKNOWN
                       else {"field": "object_name", "op": "eq", "value": satname})
    if satcatid is not None:
        clauses.append({"field": "satcat_id", "op": "eq", "value": int(satcatid)})
    if owner:
        clauses.append({"field": "owner_country", "op": "in", "value": _with_null(owner)})
    if launchvehicle:
        clauses.append({"field": "launch_vehicle_brand", "op": "in", "value": _with_null(launchvehicle)})
    if purpose:
        clauses.append({"field": "mission_category_labels", "op": "contains_any", "value": _with_null(purpose)})
    return {"version": 1, "clauses": clauses}


def filter_satellite_data(df_in, filter_table,
             status, orbit, satname, satcatid, owner, launchvehicle, purpose, year):
    '''
    Filter the app CSV with the sidebar's values through the filter spec, then place the satellites now
    (pure function: neither input is modified).

    The spec runs on the filter table built from the objects dataset (D-035); the CSV rows with the selected
    satcat_ids are kept, so the views see the same columns as before.

    @param df_in: (DataFrame) the app CSV
    @param filter_table: (DataFrame) the objects dataset's filterable fields (app.core.filter_spec)
    @param status, orbit: (list) ticked values
    @param satname, satcatid: (str or None) one satellite
    @param owner, launchvehicle, purpose: (list) selected values (empty: no filter)
    @param year: (list) [min, max], inclusive
    @return: (DataFrame) filtered rows with positions, time used, status encoded 1 (Active) / 0
    '''
    spec = sidebar_filter_spec(status, orbit, satname, satcatid, owner, launchvehicle, purpose, year)
    if spec is None:
        ids = []
    else:
        ids = filter_table.loc[filter_spec.apply(spec, filter_table), "satcat_id"].to_numpy()
    df_in = df_in[df_in["SatCatId"].isin(ids)].copy()

    # Compute satellite locations at current time
    time_now = datetime.utcnow()

    df_in[["x","y","z","lat","lon","alt"]] = compute_satloc(satrecs_for(df_in), time_now, _radius_earth__c, False)
    
    # drop only satellites SGP4 could not place; a blank descriptive field must not hide one
    df_in = df_in.dropna(subset=["x","y","z","lat","lon","alt"])
    
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
    df_path = pd.DataFrame(compute_satloc(satrecs_for(df_in.iloc[[0]])[0], time_lapse, _radius_earth__c, eci), 
                       columns =["x","y","z","lat","lon","alt"])
    df_path["Datetime"] = time_lapse
    # a satellite that decays during the period: keep only the points SGP4 could compute (hover labels need numbers)
    df_path = df_path.dropna(subset=["x","y","z","lat","lon","alt"]).reset_index(drop=True)
    df_path["xp"], df_path["yp"], df_path["zp"] = lla_to_xyz(df_path.lat,df_path.lon,df_path.alt,_radius_earth__c)    
    for col in np.setdiff1d(list(df_in.columns),list(df_path.columns)):
        df_path[col] = df_in[col].values[0]

    return df_path
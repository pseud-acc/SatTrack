#!/usr/bin/env python

"""

This module imports, merges and cleans data from the CelesTrak and UCS Satellite Catalogues

Example:

        $ python celestrak_import.py

Attributes:
    module_level_variable1 (int): 

Todo:
    * Export column distributions to csv/plots 

"""

import re # standard library

import pandas as pd # 3rd party packages
import numpy as np
import requests
from bs4 import BeautifulSoup 
from dateutil import parser
from datetime import datetime
import sqlite3

def clean_satcat_export(celestrak_dat, ucs_dat, filename):
    ''' 
    Merge CelesTrak and UCS Satellite Catalogue data

    @param celestrak_dat: (dataframe) dataframe containing CelesTrak data
    @param ucs_dat: (dataframe) dataframe containing UCS data
    @param filename: (str) name of csv file to write in clean merged satellite catalogue data
    @return: merged_satcat(dataframe) Merged and processed Satellite catalogue data
    '''    
    
    filename = ".\\dat\\clean\\" + filename #clean_satcat_data.csv"
    
    # Merge data
    merged_satcat_raw = pd.merge(celestrak_dat, ucs_dat, how="left",left_on=['NORAD_CAT_ID'],right_on=['NORAD Number'])
    
    # Remove erroneous UCS data for entry - NORAD ID 45125
    merged_satcat_clean = merged_satcat_raw.copy()
    indx = merged_satcat_clean.index[merged_satcat_clean["NORAD_CAT_ID"]==45125]
    merged_satcat_clean.loc[indx,ucs_dat.columns] = np.nan
    
    
    ## Create factor for UCS data
    merged_satcat_clean["UcsData"] =  merged_satcat_clean["NORAD Number"].apply(lambda x: 0 if np.isnan(x) else 1)

    ## Add Launch Year
    merged_satcat_clean["LaunchYear"] = merged_satcat_clean["LAUNCH_DATE"].apply(lambda x: parser.parse(x).year)

    ## Standardise Column names

    # columns to keep
    cols_to_keep_postmerge = ['NORAD_CAT_ID', 'OBJECT_ID', 'OBJECT_NAME',
     'LAUNCH_DATE', 'LaunchYear', 'LAUNCH_SITE_DESC', 'LAUNCH_SITE_COUNTRY', 'Launch Vehicle',   
     'OPS_STATUS', 'OPS_STATUS_CODE','ORBIT_CLASS', 'PERIOD', 'DECAY_DATE',
     'OWNER', 'OWNER_DESC',
     'Users', 'Purpose', 'Launch Mass (kg.)', 'Dry Mass (kg.)','Expected Lifetime (yrs.)',
    'UcsData']
    # renamed columns
    cols_renamed_postmerge = ['SatCatId', 'ObjectId', 'ObjectName', 
     'LaunchDate', 'LaunchYear', 'LaunchSite', 'LaunchSiteCountry', 'LaunchVehicle',
     'Status', 'StatusCode','OrbitClass', 'OrbitalPeriod', 'DecayDate',
     'OwnerCode', 'Owner',
     'UseType', 'Purpose','LaunchMass', 'DryMass','ExpLifetime',
    'UcsData']
    # rename columns in dataset
    merged_satcat_clean = merged_satcat_clean[cols_to_keep_postmerge].copy()
    merged_satcat_clean.rename(columns=dict([(a,b) for a,b in zip(cols_to_keep_postmerge,cols_renamed_postmerge)]), inplace=True)


    ## Fill NaN values
    for n, col_type in enumerate(merged_satcat_clean.dtypes):
        col = merged_satcat_clean.dtypes.index[n]
        if col_type == np.dtype(object):
            merged_satcat_clean[col].fillna("", inplace=True)
        else:
            merged_satcat_clean[col].fillna(-1, inplace=True)


    ## Standardise Use Type
    merged_satcat_clean["UseType"] = ["/".join(sorted([w.strip() for w in s])) for s in merged_satcat_clean["UseType"].str.split("/")]
    ind = merged_satcat_clean["UseType"] == "Earth Observation"
    merged_satcat_clean.loc[ind,"UseType"] = ""

    ## Standardise Launch Vehicle Class
    merged_satcat_clean["LaunchVehicle"] = merged_satcat_clean["LaunchVehicle"].str.strip()
    merged_satcat_clean["LaunchVehicleClass"] = [re.sub("[\s]{2,}"," ",
                                                    re.sub("[.\-\(\)]"," ",a)).rsplit(" ",1)[0].rsplit(" ",1)[0].strip() 
                                             for a in merged_satcat_clean["LaunchVehicle"]]
    def manual_mapper(dat,col,str_old,str_new):
        dat.loc[dat[col].isin(str_old), col] = str_new
        return dat
    lv_map = {"Long March":["Long"], "Soyuz":["Soyuz Fregat Soyuz"], "LauncherOne":["Launcher"],
             "Proton":["Proton/Breeze"],"ISS NRCSD":['Dextre Arm + Kaber', 'Nanoracks','J',
                                                    'KIBO','SEOPS','JEM','Kaber'],
             'JAXA M-V': ['JAXA'], 'Kaituozhe': ["KT"]}
    for u,v in lv_map.items():
        merged_satcat_clean = manual_mapper(merged_satcat_clean,"LaunchVehicleClass",v,u)

    ## Standardise Satellite Purpose
    merged_satcat_clean["Purpose"] = merged_satcat_clean["Purpose"].str.strip()
    p_map = {"Earth Observation":["Earth Observarion"], 
          "Communications":["Communication"],
          "Space Science":["Space Observation"],
           "Space Science/Technology Development": ["Space Science/Technology Demonstration"],
         "Earth Observation":["Earth Science", "Earth Observation/Earth Science","Earth Science/Earth Observation"],
          "Earth Observation/Space Observation": ["Earth/Space Observation"],
          "Communications/Navigation (Global or Regional Positioning)":["Communications/Navigation"],
         "Navigation (Global or Regional Positioning)" : ["Navigation/Global Positioning","Navigation/Regional Positioning"],
         "Educational/Technology Development": ["Technology Development/Educational"],
         "Multi-Purpose Platform":["Platform"],
         "Technology Development": ["Technology Demonstration"]}    
    for u,v in p_map.items():
        merged_satcat_clean = manual_mapper(merged_satcat_clean,"Purpose",v,u)

    ## Drop duplicate SATCAT numbers - auto
    merged_satcat_clean.drop_duplicates(inplace = True)

    ## Drop duplicate SATCAT numbers - manual
    dupl_to_drop_map = {43118: {"col": "LaunchMass", "val":10}, 43767:{"col":"LaunchMass" , "val":10}, 45123:{"col":"LaunchMass" , "val":2}, 46809:{"col":"LaunchMass" , "val":-1},
     48965:{"col":"Purpose" , "val":"Earth Observation"}, 49055:{"col":"LaunchMass" , "val":6411.0}, 49056:{"col":"LaunchMass" , "val":3852}, 49434:{"col":"LaunchVehicleClass" , "val":"Long March"},
     49818:{"col":"ExpLifetime" , "val":-1}}

    indices_to_drop = list()
    for catid,cv in dupl_to_drop_map.items():
        ind = merged_satcat_clean[(merged_satcat_clean["SatCatId"] == catid) & (merged_satcat_clean[cv["col"]] == cv["val"])].index[0]
        indices_to_drop.append(ind)

    merged_satcat_clean = merged_satcat_clean.drop(indices_to_drop, axis=0)
    
    ## Export data
    merged_satcat_clean.to_csv(filename, index=False)
    
    return merged_satcat_clean.shape, merged_satcat_clean.columns
    
    
def satcat_sql_dump(satcat_filename, dbs_name):
    ''' 
    Dump merged satellite catalogue data into SQL database

    @param satcat_filename: (str) csv containing clean satellite data
    @param dbs_name: (str) name of sqlite database to write in merged satallite catalogue data
    '''    
    
    # Define columns to keep
    cols_to_keep = ["SatCatId", "ObjectName", "LaunchYear","OrbitalPeriod", "LaunchMass", 
                    "StatusCode", "Status", "UcsData", "OrbitClass", "LaunchSiteCountry", 
                    "Owner", "UseType", "Purpose", "LaunchVehicleClass"]
    
    filename = ".\\dat\\clean\\" + satcat_filename
    
    satcat_dat = pd.read_csv(filename)
    
    satcat_dat = satcat_dat[cols_to_keep]
    
    # Fill empty entries in string columns with Unknown
    for n, col_type in enumerate(satcat_dat.dtypes):
        col = satcat_dat.dtypes.index[n]
        if col_type == np.dtype(object):
            satcat_dat[col].fillna("Unknown", inplace=True)
            
    # Check columns distributions - will export to csv
    print("Distribution Checks on satcat sql table:")
    print("")
    for col in cols_to_keep[6:]:
        print(col)
        print("-------------")
        print(satcat_dat[col].value_counts())
        print("============")
    
    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()
    
    ## Create Satellite Catalogue table in database
    satcat_dat.to_sql("satcat", conn, if_exists="replace", index=False)
    conn.commit()
    
    print("Satellite Catalogue database successfully updated")

    
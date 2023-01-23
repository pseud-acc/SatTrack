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
import nltk

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
    
    # Remove erroneous UCS data for unidentified entries
    ucs_error_ids = [45123,45125]
    merged_satcat_clean = merged_satcat_raw.copy()
    indx = merged_satcat_clean.index[merged_satcat_clean["NORAD_CAT_ID"].isin(ucs_error_ids)]
    merged_satcat_clean.loc[indx,ucs_dat.columns] = np.nan
    
    ## Remove duplicates from UCS data - take closest satellite name match between Celestrak and UCS
    dup_indx = merged_satcat_raw.NORAD_CAT_ID.value_counts().index[merged_satcat_raw.NORAD_CAT_ID.value_counts()>1]
    indx_to_drop = []
    for norad_dup in dup_indx:
        a0 = celestrak_dat[celestrak_dat["NORAD_CAT_ID"]==norad_dup]["OBJECT_NAME"].values[0].upper().strip()
        edit_dist = np.array([(nltk.edit_distance(a0,str(a).upper().strip()),ind)
                    for ind,a in merged_satcat_clean[merged_satcat_clean["NORAD_CAT_ID"]==norad_dup]["Current Official Name of Satellite"].items() ])
        indx_list = np.array(list(zip(*edit_dist))[1])
        indx_to_drop.append(indx_list[np.argmax(np.array(list(zip(*edit_dist))[0]))])
    merged_satcat_clean.drop(merged_satcat_clean.index[indx_to_drop], inplace = True)   
    
    ## Create factor for UCS data
    merged_satcat_clean["UcsData"] =  merged_satcat_clean["NORAD Number"].apply(lambda x: 0 if np.isnan(x) else 1)

    ## Add Launch Year
    merged_satcat_clean["LaunchYear"] = merged_satcat_clean["LAUNCH_DATE"].apply(lambda x: parser.parse(x).year)

    ## Standardise Column names

    # columns to keep
    cols_to_keep_postmerge = ['NORAD_CAT_ID', 'OBJECT_ID', 'OBJECT_NAME',
     'LAUNCH_DATE', 'LaunchYear', 'LAUNCH_SITE_DESC', 'LAUNCH_SITE_COUNTRY', 'Launch Vehicle',   
     'OPS_STATUS', 'OPS_STATUS_CODE','ORBIT_CLASS_EST', 'PERIOD', 'DECAY_DATE',
     'OWNER', 'OWNER_DESC','INCLINATION',
     'Users', 'Purpose', 'Launch Mass (kg.)', 'Dry Mass (kg.)','Expected Lifetime (yrs.)',
    'UcsData']
    # renamed columns
    cols_renamed_postmerge = ['SatCatId', 'ObjectId', 'ObjectName', 
     'LaunchDate', 'LaunchYear', 'LaunchSite', 'LaunchSiteCountry', 'LaunchVehicle',
     'Status', 'StatusCode','OrbitClassEstimated', 'OrbitalPeriod', 'DecayDate',
     'OwnerCode', 'Owner','Inclination',
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
    lv_map = {"Long March":["Long"], "Soyuz":["Soyuz Fregat Soyuz","11A510"], "LauncherOne":["Launcher"],
             "Proton":["Proton/Breeze"],"ISS NRCSD":['Dextre Arm + Kaber', 'Nanoracks','J',
                                                    'KIBO','SEOPS','JEM','Kaber'],
             'JAXA M-V': ['JAXA'], 'Kaituozhe': ["KT"]}
    for u,v in lv_map.items():
        merged_satcat_clean = manual_mapper(merged_satcat_clean,"LaunchVehicleClass",v,u)

    ## Standardise Satellite Purpose
    merged_satcat_clean["Purpose"] = merged_satcat_clean["Purpose"].str.strip()
    p_map = {"Communications":["Communication"],
          "Space Science":["Space Observation"],
           "Space Science/Technology Development": ["Space Science/Technology Demonstration"],
         "Earth Observation":["Earth Observarion","Earth Science", "Earth Observation/Earth Science","Earth Science/Earth Observation"],
          "Earth Observation/Space Science": ["Earth/Space Observation"],
          "Communications/Navigation (Global or Regional Positioning)":["Communications/Navigation"],
         "Navigation (Global or Regional Positioning)" : ["Navigation/Global Positioning","Navigation/Regional Positioning"],
         "Educational/Technology Development": ["Technology Development/Educational"],
         "Multi-Purpose Platform":["Platform"],
         "Technology Development": ["Technology Demonstration"]}    
    for u,v in p_map.items():
        merged_satcat_clean = manual_mapper(merged_satcat_clean,"Purpose",v,u)
    
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
                    "StatusCode","Inclination", "Status", "UcsData", "OrbitClassEstimated", "LaunchSiteCountry", 
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
    for col in cols_to_keep[7:]:
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

    
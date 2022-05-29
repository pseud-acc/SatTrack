#!/usr/bin/env python

"""

This module imports and cleans data from the CelesTrak Satellite Catalogue (see: https://celestrak.com/)

Example:

        $ python celestrak_import.py

Function:
    celestrak_update_check: Check whether Celestrak website has been updated since last download metadata csv file 
    map_table: Extract code description tables from Celestrak website
    import_celestrak_satcat: Import Celestrak satellite catalogue, clean and export to csv
    
Todo:
    * 

"""

import re # standard library

import pandas as pd # 3rd party packages
import numpy as np
import requests
from bs4 import BeautifulSoup 
from dateutil import parser
from datetime import datetime

def celestrak_update_check(metadata_location, tle_check):
    ''' 
    Check whether CelesTrak Satellite Catalogue download needs updating.

    @param url: (str) website url to Celestrak page
    @param tle_check: (boolean) If true, check TLE metadata
    @param metadata_location: (str) filename of CelesTrak download metadata
    @return: (boolean, str) True - download CelesTrak data, Last update date in string format
    '''    
    
    if tle_check: 
        dat_source = "Celestrak_TLE"
        url = "https://celestrak.com/NORAD/elements/"
    else:
        dat_source = "Celestrak"
        url = "https://celestrak.com/satcat/search.php"
        
    # Check date of most recent data update on CelesTrak website
    #url = "https://celestrak.com/satcat/search.php" Satellite catalogue
    #url = "https://celestrak.com/NORAD/elements/" TLE
    html = requests.get(url = url).text
    soup = BeautifulSoup(html, "html.parser")
    last_update_str = re.findall("Current as of (.*) UTC",str(soup))[0]
    last_update = parser.parse(last_update_str, dayfirst=True)

    # Check date of most recent download
    filename = metadata_location #"..\dat\\meta\\last_data_update.csv"
    metadata = pd.read_csv(filename)
    metadata_last_download = metadata[metadata["Source"] == dat_source]["Last Download"].values[0]
    print("Last Celestrak download: ",  metadata_last_download)    
    if parser.parse(metadata_last_download, dayfirst=True) < last_update:
        today = datetime.now()
        metadata.loc[metadata["Source"] == dat_source,"Last Download"] = today.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.loc[metadata["Source"] == dat_source,"Last Update"] = last_update.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.to_csv(filename, index=False)
        return True, last_update_str
    else:
        return False, last_update_str
    
def map_table(url, col_name):
    ''' 
    map_table imports html table from CelesTrak website. Tables contain a description of each code assigned under columns in the satellite catalogue

    @param url: website url to Celestrak page containing table with code and description
    @param col_name: column name for list of codes. Accompanying description is assigned column name, [col_name]_DESC.
    @return: pandas dataframe containing code and description
    '''
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup

    html = requests.get(url = url).text
    soup = BeautifulSoup(html, "html.parser")
    tags = soup("tbody")
    tbl_map = pd.DataFrame([[td.get_text() for td in tr.findAll("td")] for tr in tags[0].findAll("tr")],
                           columns = [col_name,col_name + "_DESC"])
    for col in tbl_map.columns:
        tbl_map[col] = tbl_map[col].str.strip()
    return tbl_map

    
def import_celestrak_satcat(filename, download_file):
    ''' 
    Import CelesTrak Satellite Catalogue data

    @param url_owner: (str) website url to Celestrak page containing Owner code and description
    @param url_launchsite: (str) website url to Celestrak page containing Launch Site code and description    
    @param url_satcat: (str) website url to Celestrak page containing satellite catalogue csv   
    @param filename: (str) name of csv file to write in clean CelesTrak data
    @param download_file: (Boolean) If True download satellite catalogue csv from Celestrak website
    @return: (dataframe) processed data from satellite catalogue 
    '''        
    
    filename_clean = ".\\dat\\clean\\" + filename #celestrak_satcat.csv"
    
    if download_file == False:
        return pd.read_csv(filename_clean)
    else:
    
        ## DATA IMPORT ##

        # Import Owner code descriptions
        url = "https://celestrak.com/satcat/sources.php"
        owner_map = map_table(url, "OWNER")
        owner_clean_map = {'United States':'USA', "United Kingdom":"UK",
           'Republic of Korea':'South Korea', 'Republic of Rwanda':'Rwanda', 'Republic of Tunisia':'Tunisia',
           'United States/Brazil':'US/Brazil', 'United Arab Emirates':'UAE',
           'Republic of Paraguay':'Paraguay', 'European Space Agency':'ESA',
           'Asia Broadcast Satellite':'ABS', "People's Republic of China":'China',
            'Taiwan (Republic of China)':"Taiwan", 'International Space Station':"ISS",
           'Peoples Republic of Bangladesh':'Bangladesh',
           'Republic of the Union of Myanmar':'Myanmar',
           'North Atlantic Treaty Organization':'NATO',
           "Democratic People's Republic of Korea":'North Korea',
           'Czech Republic (former Czechoslovakia)':'Czech Republic',
           'Philippines (Republic of the Philippines)':'Philippines',
           'Arab Satellite Communications Organization':'Arabsat',
           'Commonwealth of Independent States (former USSR)':'Russia/USSR',
           'Asia Satellite Telecommunications Company (ASIASAT)':'ASIASAT',
           'International Mobile Satellite Organization (INMARSAT)':'INMARSAT',
           'European Telecommunications Satellite Organization (EUTELSAT)':'EUTELSAT',
           'International Telecommunications Satellite Organization (INTELSAT)':'INTELSAT',
           'European Organization for theExploitation of Meteorological Satellites (EUMETSAT)':'EUMETSAT'}
        owner_map["OWNER_DESC"] = owner_map["OWNER_DESC"].apply(lambda x: owner_clean_map[x] if x in owner_clean_map.keys() else x)

        # Import Launch Site code descriptions
        url = "https://celestrak.com/satcat/launchsites.php"
        launch_site_map = map_table(url, "LAUNCH_SITE")
        launch_site_map["LAUNCH_SITE_COUNTRY"] = [s[-1].strip().split("(")[0].strip().replace(")","") for s in       launch_site_map["LAUNCH_SITE_DESC"].str.split(",")]
        launch_site_map.loc[launch_site_map["LAUNCH_SITE"] == "SNMLP","LAUNCH_SITE_COUNTRY"] = "Kenya"

        # Download satellite catalogue as csv
        #csv_url  = "https://celestrak.com/pub/satcat.csv"
        #filename = "data\satcat.csv"

        filename_raw = ".\\dat\\raw\\celestrak_satcat.csv"

        url = "https://celestrak.com/pub/satcat.csv"
        data = requests.get(url)
        with open(filename_raw, "wb") as f: f.write(data.content)
        all_sat_raw = pd.read_csv(filename_raw)

        ## DATA PROCESSING ##

        # Select features to keep
        cols_to_keep_ctk = ['OBJECT_NAME', 'OBJECT_ID', 'NORAD_CAT_ID', 'OBJECT_TYPE','OPS_STATUS_CODE',
               'OWNER', 'LAUNCH_DATE', 'LAUNCH_SITE', 'DECAY_DATE',
               'PERIOD', 'ORBIT_CENTER', 'ORBIT_TYPE']
        all_sat_clean = all_sat_raw[cols_to_keep_ctk]

        # Filter by Earth Orbiting Satellites
        all_sat_clean = all_sat_clean[(all_sat_raw["OBJECT_TYPE"] == "PAY") & (all_sat_clean["ORBIT_CENTER"] == "EA") & (all_sat_clean["ORBIT_TYPE"] == "ORB")]

        # Function to create Orbit Class factor (LEO, MEO, GEO, HEO) using Orbital Period
        def orbit_class(row):
            leo_hi = 130
            geo_lo = 1400
            geo_hi = 1500
            period = row["PERIOD"]
            if period <= leo_hi:
                row["ORBIT_CLASS"] = "LEO"
            elif period > leo_hi and period < geo_lo:
                row["ORBIT_CLASS"] = "MEO"
            elif period >= geo_lo and period <= geo_hi:
                row["ORBIT_CLASS"] = "GEO"
            elif period > geo_hi:
                row["ORBIT_CLASS"] = "HEO"

            return row    

        all_sat_clean = all_sat_clean.apply(lambda x: orbit_class(x), axis=1)

        # Create factor for Operational Status
        all_sat_clean.loc[all_sat_clean["OPS_STATUS_CODE"].isna(),"OPS_STATUS_CODE"] = "UNK" # Set all Nans as Unk -> raw data had "?"
        active_codes = ["+", "P", "B", "S", "X"] # Set operational status as Active if code is in list - defined in "https://celestrak.com/satcat/status.php"
        all_sat_clean["OPS_STATUS"] = all_sat_clean["OPS_STATUS_CODE"].apply(lambda x: "Active" if x in active_codes else "Inactive")    

        # Merge on owner and launch site data (from mapping tables)
        all_sat_clean = pd.merge(all_sat_clean, owner_map, how="left", on=["OWNER"]) #Owner
        all_sat_clean = pd.merge(all_sat_clean, launch_site_map, how="left", on=["LAUNCH_SITE"]) #Launch Site  

        # Export clean data
        all_sat_clean.to_csv(filename_clean, index=False)
    
    return all_sat_clean
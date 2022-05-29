#!/usr/bin/env python

"""

This module imports and cleans data from the UCS Satellite Catalogue (see: https://www.ucsusa.org)

Example:

        $ python ucs_import.py

Function:
    ucs_update_check: Check whether UCS satellite catalogue has been updated since last download metadata csv file 
    import_ucs_satcat: Import UCS satellite catalogue, clean and export to csv
    

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

def ucs_update_check(metadata_location):
    ''' 
    Check whether UCS Satellite Catalogue download needs updating.

    @param url: (str) website url to UCS page containing table with code and description
    @param metadata_location: (str) filename of UCS download metadata
    @return: (boolean, str) True - download UCS data, Last update date in string format
    '''
    
    url = "https://www.ucsusa.org/resources/satellite-database"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    last_update_str = re.findall(">Updated (.*)<",str(soup))[0]
    last_update = parser.parse(last_update_str, dayfirst=True)
    
    # Check download metadata
    filename = metadata_location#"data\last_data_update.csv"
    metadata = pd.read_csv(filename)
    metadata_last_download = metadata[metadata["Source"] == "UCS"]["Last Download"].values[0]
    print("Last UCS download: ",  metadata_last_download)
    if parser.parse(metadata_last_download, dayfirst=True) < last_update:
        today = datetime.now()
        metadata.loc[metadata["Source"] == "UCS","Last Download"] = today.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.loc[metadata["Source"] == "UCS","Last Update"] = last_update.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.to_csv(filename, index=False)
        return True, last_update_str        
    else:
        return False, last_update_str        
    
def import_ucs_satcat(filename, download_file):
    ''' 
    Import UCS satellite catalogue

    @param url_ucs: (str) website url to UCS page containing satellite catalogue csv   
    @param filename: (str) name of csv file to write in clean UCS data 
    @param download_file: (Boolean) If True download satellite catalogue xls file from UCS website    
    @return: (dataframe) processed data from satellite catalogue 
    '''        
    
    filename_clean = ".\\dat\\clean\\" + filename #ucs_satcat.csv"
    
    if download_file == False:
        return pd.read_csv(filename_clean)
    else:    
        ## DATA IMPORT ## 

        filename_raw = ".\\dat\\raw\\ucs_satcat.xls" #celestrak_satcat.csv"

        # Import UCS Satellite catalogue
        url = "https://www.ucsusa.org/resources/satellite-database"
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")        
        tags = soup("a")
        for tag in tags:
            if tag.get_text() == "Database": 
                file_url = "https://www.ucsusa.org" + tag.get("href")# "https://www.ucsusa.org" + tag.get("href")
                break
        with open(filename_raw, "wb") as f:
            r = requests.get(file_url)
            f.write(r.content)
            f.close()
        ucs_sat_raw = pd.read_excel(filename_raw)

        ## DATA PROCESSING ##

        # Select features to keep
        cols_to_keep_ucs = ['Current Official Name of Satellite','Country of Operator/Owner', 'Operator/Owner', 'Users', 'Purpose',
               'Detailed Purpose', 'Class of Orbit', 'Type of Orbit','Date of Launch',
               'Launch Mass (kg.)', 'Dry Mass (kg.)', 'Power (watts)',
                'Expected Lifetime (yrs.)','Launch Vehicle','NORAD Number']
        ucs_sat_clean = ucs_sat_raw.copy()[cols_to_keep_ucs]

        # Convert NORAD Catalogue number to int
        ucs_sat_clean = ucs_sat_clean[~ucs_sat_clean["NORAD Number"].isna()]
        ucs_sat_clean["NORAD Number"] = ucs_sat_clean["NORAD Number"].astype('int64')    

        ucs_sat_clean.to_csv(filename_clean, index=False)

        return ucs_sat_clean
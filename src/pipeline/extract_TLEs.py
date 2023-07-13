#!/usr/bin/env python

"""

This module extracts General Perturbations (GP) Element sets from Celestrak website and exports to SQL database.

Example:

        $ python extract_TLEs.py

Function:
    extract_TLE_active: Extract active satellite TLE data
    extract_TLE: Extract TLE data for list of SATCAT Ids
    export_satcat_tle: Merge satellite catalogue and TLE data - export to csv

Todo:
    * 

"""

import re

import pandas as pd
import numpy as np

import http
import sqlite3
import requests
from requests.adapters import HTTPAdapter, Retry
import time
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import datetime

set_retry_count = 5

def request_celestrak_data(url, retry_count):
    ''' 
    Request data from Celestrak website with retries

    @param url: (str) url containing TLE data for specific SatCat ID 
    @param retry_count: (integer) number of times to retry connection
    @return: data (list): list of strings containing TLE data if connection attempt(s) successful, otherwise None
    '''         
    try:
        s = requests.Session()
        retries = Retry(total=retry_count,
                        backoff_factor=1) #waits 0s, 1s, 4s, 8s, ... between retry attempts
        s.mount('https://', HTTPAdapter(max_retries=retries))
        data = s.get(url).text.splitlines() 
        print("Connection attempt was successful")
        s.close()
        return data
    except Exception:
        pass 
        print("Connection retry count limit of ", retry_count, " exceeded.")
        return

def map_celestrak_data(data_in, sat): 
    ''' 
    Map TLE data extracted from Celestrak to array format to insert in database

    @param sat: (str) SatCat ID 
    @param data_in: (list) raw TLE data in list format
    @return: data_mapped: dataframe containing TLE data
    '''     
    print("Check if data is present")
    data_array = [d.strip() for d in data_in] + [sat]
    data_mapped   = pd.DataFrame([data_array], columns=["ObjectName","TLE1","TLE2","SatCatId"])
    print("=== Data extracted ===")
    return data_mapped

def extract_TLE_active(dbs_name, lastupdate):
    ''' 
    Bulk extract TLEs of active satellites from Celestrak website.

    @param dbs_name: (str) database name (sqlite) to export TLEs
    @param lastupdate: (str) Datetime of last update of Celestrak TLEs
    @return: (missing_satcat, length) list of SATCAT Ids w/o TLEs, int number of SATCAT Ids w/ extracted TLEs
    '''    
    
    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()
    
    ## Extract SATCAT Number list
    query = "SELECT satcatid FROM satcat"
    cur.execute(query)
    ids = cur.fetchall()

    sat_list_satcat_all = pd.Series([a[0] for a in ids])
    
    ## Define API access url
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    
    ## Call API data
    data = requests.get(url).text.split("\n")
    if len(data) == 1:
        return "=== Failure to Retrieve ==="
        
    data = [d.strip() for d in data]
    df = np.reshape(np.array(data[:-1]),(int(len(data[:-1])/3),3))
    df_tle = pd.DataFrame(df, columns=["ObjectName","TLE1","TLE2"])
    df_tle["LastUpdate"] = lastupdate
    
    ## Extract SATCAT Numbers
    sat_list_satcat_act = df_tle["TLE1"].str.extract("^1 ([\d]{1,})U.*").astype("int")[0]
    df_tle["SatCatId"] = sat_list_satcat_act    
    
    # Missing SATCAT Numbers
    missing_satcat = list(set(sat_list_satcat_all) - set(sat_list_satcat_act))
 
    ## Add to SQL database
    df_tle.to_sql("tle", conn, if_exists="replace", index=False)
    conn.commit()
    
    return missing_satcat, len(sat_list_satcat_act)
    
def extract_TLE(dbs_name, lastupdate, satcatid_list):
    ''' 
    Extract TLE data of satellites individually from Celestrak website.

    @param dbs_name: (str) database name (sqlite) to export TLEs
    @param lastupdate: (str) Datetime of last update of Celestrak TLEs
    @param satcatid_list: (list) int list of SATCAT Ids for which to request TLE data
    @return: (satcat_no_data) list of SATCAT Ids with no TLE data
    '''
    
    
    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()    
    
    ## Define API access url    
    service_url = "https://celestrak.org/NORAD/elements/gp.php?CATNR={:}&FORMAT=tle"
    
    # API Call to Celestrak
    satcat_no_data = []
    start = time.time()
    
    count=0
    ## Loop through list of SATCAT Numbers 
    for sat in satcatid_list:

        # Check database
        query = "select lastupdate from tle where satcatid = {}".format(sat)
        cur.execute(query)
        lu = cur.fetchone()

        if lu is not None:
            # Update TLE data for existing entry
            if lu[0] != lastupdate:
                    # Create API request url using satellite name
                    url = service_url.format(sat)
                    #url = "https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
                    print("Retrieving", url)
                    # try retrieving TLE data from celestrak
                    api_data = request_celestrak_data(url, set_retry_count)          
                    # try mapping celestrak data
                    try:
                        tmp = map_celestrak_data(api_data, sat)
                    except Exception:
                        pass 
                        print("=== Failure to Retrieve ===")
                        print(api_data)
                        satcat_no_data.append(sat)
                        continue

                    tmp   = pd.DataFrame([data1], columns=["ObjectName","TLE1","TLE2","SatCatId"])
                    query = 'UPDATE tle  SET  ObjectName = "{obj}", TLE1 = "{t1}", TLE2 = "{t2}", LastUpdate = "{lu}", WHERE SatCatId = {sid}'.format(obj = tmp["ObjectName"][0],t1 = tmp["TLE1"][0], lu=lastupdate,
                                                      t2 = tmp["TLE2"][0], sid = tmp["SatCatId"][0])
               # print(query)
            else:
                continue
        else:    
            # Create API request url using satellite name
            url = service_url.format(sat)
            print("Retrieving", url)
            # try retrieving TLE data from celestrak
            api_data = request_celestrak_data(url, set_retry_count)          
            # try mapping celestrak data
            try:
                tmp = map_celestrak_data(api_data, sat)
            except Exception:
                pass 
                print("=== Failure to Retrieve ===")
                print(api_data)
                satcat_no_data.append(sat)
                continue
            # Insert TLE data for new entry
            query = 'INSERT INTO tle (ObjectName,TLE1,TLE2,LastUpdate,SatCatId)  VALUES("{obj}","{t1}","{t2}","{lu}",{sid})'.format(
            obj = tmp["ObjectName"][0],t1 = tmp["TLE1"][0], t2 = tmp["TLE2"][0], lu=lastupdate, sid = tmp["SatCatId"][0])

        cur.execute(query)

        count = count + 1
        print(count)
        # Batch save every 10 TLEs
        if count % 10 == 0:
            conn.commit()
            print("Committing to database...")
            
    conn.commit()
    end = time.time()    
    print(end-start)    
    
    print("Individual Satellite TLE update complete!")    
    
    return satcat_no_data
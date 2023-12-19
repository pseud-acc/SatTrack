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
                        backoff_factor=1)  # waits 0s, 1s, 4s, 8s, ... between retry attempts
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
    if len(data_in) == 3:
        data_array = [d.strip() for d in data_in] + [sat]
        data_mapped = pd.DataFrame([data_array], columns=["ObjectName", "TLE1", "TLE2", "SatCatId"])
        print("=== Data extracted ===")
        return True, data_mapped
    elif data_in[0] == 'No GP data found':
        print(data_in)
        return True, None
    elif re.search('(.*)temporarily blocked(.*)', ''.join(data_in)) is not None:
        print("")
        print("Celestrak API request limit reached - connection temporarily blocked.")
        print("")
        print("Exiting...")
        print("")
        exit()


def insert_tle(tle_data, satcatid_in, lastupdate_in, cur_in, conn_in):
    '''
    Build and execute parameterised query to insert TLE data into sqlite database

    @param tle_data: (dataframe) table containing satellite name and TLE data
    @param satcatid_in: (integer) Satcat number for satellite
    @param lastupdate_in: (string) Last update date of TLE data in celestrak database
    @param cur_in: (string) Cursor object for sqlite database connection
    @param conn_in (string) Sqlite database connection
    @return: None
    '''
    query = '''INSERT INTO tle (SatCatId, ObjectName, 
                                TLE1, TLE2, LastUpdate, InsertedDateTime)  
                VALUES({sid},"{obj}","{t1}","{t2}","{lu}","{dt}")'''.format(
        sid=satcatid_in,
        obj=tle_data["ObjectName"][0],
        t1=tle_data["TLE1"][0],
        t2=tle_data["TLE2"][0],
        lu=lastupdate_in,
        dt=datetime.today().strftime("%d/%m/%Y, %H:%M:%S")
    )

    cur_in.execute(query)
    conn_in.commit()
    return


def update_tle(tle_data, satcatid_in, lastupdate_in, cur_in, conn_in):
    '''
    Build and execute parameterised query to update TLE data into sqlite database

    @param tle_data: (dataframe) table containing satellite name and TLE data
    @param satcatid_in: (integer) Satcat number for satellite
    @param lastupdate_in: (string) Last update date of TLE data in celestrak database
    @param cur_in: (string) Cursor object for sqlite database connection
    @param conn_in (string) Sqlite database connection
    @return: None
    '''
    query = '''
            UPDATE tle  
            SET  ObjectName = "{obj}"
            , TLE1 = "{t1}"
            , TLE2 = "{t2}"
            , LastUpdate = "{lu}"
            , InsertedDateTime = "{dt}"
            WHERE SatCatId = {sid}'''.format(
        obj=tle_data["ObjectName"][0],
        t1=tle_data["TLE1"][0],
        lu=lastupdate_in,
        t2=tle_data["TLE2"][0],
        dt=datetime.today().strftime("%d/%m/%Y, %H:%M:%S"),
        sid=satcatid_in)

    cur_in.execute(query)
    conn_in.commit()
    return


def remove_decayed_TLE(dbs_name):
    """
    Remove decayed satellites from TLE database

    @param dbs_name: (str) database name (sqlite) to export TLEs
    @return: None
    """

    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()

    ## Delete records from target
    query = '''
        DELETE FROM tle
        WHERE SatCatId NOT IN (
        SELECT SatCatId FROM satcat)    
    '''
    cur.execute(query)
    conn.commit()

    return


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
    data = request_celestrak_data(url, set_retry_count)

    # Check data length - should be >1k lines
    data_len = len(data)

    if data_len < 1000:
        if data_len == 1:
            return "=== Failure to Retrieve ==="
        elif re.search('(.*)temporarily blocked(.*)', ''.join(data)) is not None:
            print("")
            print("Celestrak API request limit reached - connection temporarily blocked.")
            print("")
            print("Exiting...")
            print("")
            exit()

    data = [d.strip() for d in data]
    df = np.reshape(np.array(data), (int(len(data) / 3), 3))
    df_tle = pd.DataFrame(df, columns=["ObjectName", "TLE1", "TLE2"])
    df_tle["LastUpdate"] = lastupdate

    ## Extract SATCAT Numbers
    sat_list_satcat_act = df_tle["TLE1"].str.extract("^1 ([\d]{1,})U.*").astype("int")[0]
    df_tle["SatCatId"] = sat_list_satcat_act

    # Add insert time
    df_tle["InsertedDateTime"] = datetime.today().strftime("%d/%m/%Y, %H:%M:%S")

    # Reorder columns
    df_tle = df_tle[["SatCatId", "ObjectName", "TLE1", "TLE2", "LastUpdate", "InsertedDateTime"]]

    # -- Upsert TLEs

    ## Create TLE table if it does not exist
    query = '''
            CREATE TABLE IF NOT EXISTS tle (
                SatCatId INTEGER,
                ObjectName TEXT,
                TLE1 TEXT,
                TLE2 TEXT,
                LastUpdate TEXT,                
                InsertedDateTime TEXT
            )
           '''
    cur.execute(query)
    conn.commit()

    ## Add new data to staging table
    df_tle.to_sql("tle_staging", conn, if_exists="replace", index=False)
    conn.commit()

    ## Delete records from target
    query = '''
    DELETE FROM tle
    WHERE SatCatId IN (
    SELECT SatCatId FROM tle_staging)    
    '''
    cur.execute(query)
    conn.commit()

    ## Insert staging data into target
    query = '''
    INSERT INTO tle
    SELECT 
        SatCatId    
        , ObjectName
        , TLE1
        , TLE2
        , LastUpdate
        , InsertedDateTime
    FROM tle_staging
    '''
    cur.execute(query)
    conn.commit()

    # Find missing SATCAT Numbers
    missing_satcat = list(set(sat_list_satcat_all) - set(sat_list_satcat_act))

    return True, missing_satcat, len(sat_list_satcat_act)


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

    # Convert list of missing satcatids to dataframe
    missing_satcat_df = pd.DataFrame(satcatid_list, columns=['SatCatId'])

    # insert list into table - replace
    missing_satcat_df.to_sql("missing_tle", conn, if_exists="replace", index=False)
    conn.commit()

    # join w/ TLE data and pull out last update, extract ordered by last update ascending - new satcatids ordered first
    # only checks TLE data if TLE has been extracted before (extract contains Object name, TLE1 and TLE2)
    query = '''
        SELECT
            s.SatCatId,
            t.LastUpdate
        FROM 
            missing_tle s
        LEFT JOIN
            tle t
        ON
            s.SatCatId = t.SatCatId
        WHERE t.ObjectName != "" OR t.ObjectName IS NULL 
        ORDER BY LastUpdate
    '''
    cur.execute(query)

    missing_satcat_raw = cur.fetchall()

    # Convert to data frame
    missing_satcat_w_lu = pd.DataFrame(missing_satcat_raw, columns=['SatCatId', 'LastUpdate'])

    # map to list
    missing_satcat_list = missing_satcat_w_lu['SatCatId'].to_list()

    # Extract satcatids where TLE was missing at last update -
    # ensures newest satcatids will be checked first (null in above query)
    query = '''
        SELECT
            SatCatId
        FROM tle
        WHERE ObjectName = ""
        ORDER BY LastUpdate
    '''
    cur.execute(query)

    historic_missing_satcat_raw = cur.fetchall()

    # Convert to data frame
    historic_missing_satcat = pd.DataFrame(historic_missing_satcat_raw, columns=['SatCatId'])

    # Append list of historic missing satcats to original list
    missing_satcat_list = missing_satcat_list + historic_missing_satcat['SatCatId'].to_list()

    count = 0
    ## Loop through list of SATCAT Numbers
    for n, sat in enumerate(missing_satcat_list):
        print("Checking ", n + 1, "/", len(missing_satcat_list), " satellites")
        # Check database
        query = "select lastupdate from tle where satcatid = {}".format(sat)
        cur.execute(query)
        lu = cur.fetchone()

        if lu is not None:
            print("Update TLE data for existing entry")
            print("New date:", parser.parse(lastupdate).date(), "Existing date:", parser.parse(lu[0]).date())
            if parser.parse(lu[0]).date() != parser.parse(lastupdate).date():
                # Create API request url using satellite name
                url = service_url.format(sat)
                # url = "https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
                print("Retrieving", url)
                # try retrieving TLE data from celestrak
                api_data = request_celestrak_data(url, set_retry_count)
                # try mapping celestrak data
                extract_is_not_blocked, tmp_data = map_celestrak_data(api_data, sat)
                if extract_is_not_blocked:
                    if tmp_data is None:
                        print("=== Failure to Retrieve ===")
                        print(api_data)
                        satcat_no_data.append(sat)
                        null_data = pd.DataFrame([['', '', '', '']], columns=["ObjectName", "TLE1", "TLE2", "SatCatId"])
                        update_tle(null_data, sat, lastupdate, cur, conn)
                        continue
                    else:
                        update_tle(tmp_data, sat, lastupdate, cur, conn)
                else:
                    print("")
                    print("Celestrak API request limit reached - connection temporarily blocked.")
                    print("")
                    print("Exiting...")
                    print("")
                    satcat_no_data = satcat_no_data + missing_satcat_list[n:]
                    end = time.time()
                    print("Time taken to extract individual TLEs", end - start)
                    print("Individual Satellite TLE update complete!")
                    return satcat_no_data
            else:
                continue
        else:
            print("Insert TLE data for new entry")
            # Create API request url using satellite name
            url = service_url.format(sat)
            print("Retrieving", url)
            # try retrieving TLE data from celestrak
            api_data = request_celestrak_data(url, set_retry_count)
            # try mapping celestrak data
            extract_is_not_blocked, tmp_data = map_celestrak_data(api_data, sat)
            if extract_is_not_blocked:
                if tmp_data is None:
                    print("=== Failure to Retrieve ===")
                    print(api_data)
                    satcat_no_data.append(sat)
                    # Insert nulls for satcatid entry w/o TLE data
                    null_data = pd.DataFrame([['', '', '', '']], columns=["ObjectName", "TLE1", "TLE2", "SatCatId"])
                    insert_tle(null_data, sat, lastupdate, cur, conn)
                    continue
                else:
                    # Insert TLE data for new entry
                    insert_tle(tmp_data, sat, lastupdate, cur, conn)
            else:
                print("")
                print("Celestrak API request limit reached - connection temporarily blocked")
                satcat_no_data = satcat_no_data + missing_satcat_list[n:]
                end = time.time()
                print("Time taken to extract individual TLEs", end - start)
                print("Individual Satellite TLE update complete!")
                return satcat_no_data

        count = count + 1
        print("TLEs successfully extracted for ", count, " satellites")
        # Batch save every 10 TLEs
        if count % 10 == 0:
            conn.commit()
            print("Committing to database...")

    conn.commit()
    end = time.time()
    print("Time taken to extract individual TLEs", end - start)

    print("Individual Satellite TLE update complete!")

    return satcat_no_data

def drop_staging_tables(dbs_name):
    '''
    Remove decayed satellites from TLE database

    @param dbs_name: (str) database name (sqlite) to export TLEs
    @return: None
    '''

    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()

    staging_tables = ["tle_staging", "missing_tle"]

    ## Delete staging tables from database
    for table in staging_tables:
        query = '''
            DROP TABLE IF EXISTS {table_name};
        '''.format(table_name = table)
        cur.execute(query)
        conn.commit()

    ## Reclaim unused space from database
    query = '''
        VACUUM;
    '''
    print(query)
    cur.execute(query)
    conn.commit()

    return
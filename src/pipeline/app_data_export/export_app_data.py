#!/usr/bin/env python

"""

This module joins satellite catalogue and TLE data, creates updated orbital class type and exports data to csv.

Example:

        $ python export_app_data.py

Function:
    export_satcat_tle: Merge satellite catalogue and TLE data - export to csv

Todo:
    * 

"""


import pandas as pd
import sqlite3


def export_satcat_tle(dbs_name, satcat_tle_filename):
    ''' 
    Check whether CelesTrak Satellite Catalogue download needs updating.

    @param dbs_name: (str) database name (sqlite) to export TLEs
    @param satcat_tle_filename: (str) Name of file to export merged Satellite Catalogue and TLE data
    '''    
    
    ## Connect to SQL database
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()    
        
    ## Create temporary view of merged Satcat and TLE data
    query = '''
        DROP VIEW IF EXISTS satcat_tle;
        CREATE VIEW satcat_tle
        AS
        SELECT
            s.*,
            t.TLE1,
            t.TLE2
        FROM 
            tle t
        INNER JOIN
            satcat s
        ON
            t.SatCatId = s.SatCatId
        WHERE 
            s.OrbitalPeriod > 0 AND
            t.TLE1 != "" AND
            t.TLE2 != ""
    '''
    cur.executescript(query)
    conn.commit()
    
    ## Extract merged satcat and TLE data
    # Extract table
    cur.execute("select * from satcat_tle")
    satcat_raw = cur.fetchall()
    # Extract table column names
    cur.execute("pragma table_info(satcat_tle)")
    cols = [a[1] for a in cur.fetchall()]
    # Convert to data frame
    satcat = pd.DataFrame(satcat_raw, columns = cols)
    
    ## Evaluate updated orbital class using TLEs
    
    #Extract mean motion and eccentricity from TLE
    satcat['MeanMotion'] = satcat['TLE2'].str[52:63].astype(float)
    satcat['Eccentricity'] = ('0.' + satcat['TLE2'].str[26:33]).astype(float)
    
    # Define orbit classification function
    # Low Earth Orbit (LEO): period(mins) <= 128 and eccentricity < 0.25
    # Geostationary Orbit (GEO): 0.99 <= Mean motion  <= 1.01 and eccentricity < 0.01
    # Geosynchronous Orbit (GSO): 97% * 1436 <= period(mins) <= 103% 1436 (Earth's orbital period = 1436 mins)
    # Medium Earth Orbit (MEO): 128 < period(mins) < 97% * 1436 (between LEO and GSO orbits)
    # High Earth Orbit (HEO): period(mins) > 103% * 1436 (above GSO orbits)
    def OrbitType(row):
        incl = row["Inclination"]            
        mm = row["MeanMotion"]
        ecc = row["Eccentricity"]
        p = row["OrbitalPeriod"]
        if p < 128 and ecc < 0.25:
            row["OrbitClass"] = "LEO" #Low Earth orbit
        else:
            if mm >= 0.99 and mm <= 1.01 and ecc < 0.01 and incl < 1:
                row["OrbitClass"] = "GEO" #Geostationary orbit
            elif p >= 1436*0.97 and p <= 1436*1.03:
                row["OrbitClass"] = "GSO" #Geosynchronous orbit
            elif p >= 128 and p < 1436*0.98:
                row["OrbitClass"] = "MEO" #Medium Earth orbit
            else:
                row["OrbitClass"] = "HEO" #High Earth orbit
        return row
    
    satcat = satcat.apply(lambda x: OrbitType(x), axis=1)
    
    print("Distribution Checks on satcat orbit classification:")
    print("")
    for col in ['OrbitClass']:
        print(col)
        print("-------------")
        print(satcat[col].value_counts())
        print("============")    
    
    #Drop columns
    #satcat.drop(columns=["MeanMotion","Eccentricity"], inplace = True)
    
    # Export data to csv
    filename = ".\\dat\\clean\\" + satcat_tle_filename
    
    satcat.to_csv(filename, index=False)
    
    print("Merged Satellite Catalogue-TLE data exported to csv!")
    

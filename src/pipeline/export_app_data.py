#!/usr/bin/env python

"""

This module joins satellite catalogue and TLE data and exports to csv file.

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
            s.OrbitalPeriod > 0
    '''
    cur.executescript(query)
    conn.commit()
    
    ## Extract merged satcat and TLE data to csv file
    # Extract table
    cur.execute("select * from satcat_tle")
    satcat_raw = cur.fetchall()
    # Extract table column names
    cur.execute("pragma table_info(satcat_tle)")
    cols = [a[1] for a in cur.fetchall()]
    # Export data to csv
    filename = ".\\dat\\clean\\" + satcat_tle_filename
    satcat = pd.DataFrame(satcat_raw, columns = cols)
    satcat.to_csv(filename, index=False)
    
    print("Merged Satellite Catalogue-TLE data exported to csv!")
    

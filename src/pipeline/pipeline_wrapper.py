#!/usr/bin/env python

"""

This module contains wrapper functions for the satellite catalogue and TLE data pipeline functions.

Example:

        $ python pipeline_wrapper.py

Attributes: 

Todo:
    * 

"""

import sys
import os

from celestrak_import import celestrak_update_check, import_celestrak_satcat
from ucs_import import ucs_update_check, import_ucs_satcat
from create_satcat import clean_satcat_export, satcat_sql_dump

from extract_TLEs import extract_TLE_active, extract_TLE, export_satcat_tle

def satcat_pipeline(metadata,
                    update_satcat,
                    filename_celestrak,
                    filename_ucs,
                    filename_satcat,
                    satdat_dbs,
                    commit_data):
    
    ''' 
    Run satellite catalogue pipeline.

    @param metadata_location: (str) filename of download metadata
    @param update_satcat: (boolean) If true, update satellite catalogue data (override)
    @param filename_celestrak: (str) name of csv file to write in clean CelesTrak data
    @param filename_ucs: (str) name of csv file to write in clean UCS data 
    @param filename_satcat: (str) name of csv file to write in clean merged satellite catalogue data 
    @param satdat_dbs: (str) name of sqlite database to write in merged satallite catalogue data     
    @param commit_data: (boolean) If True, commit updated satellite catalogue data to github
    '''    
    
    # >>> Page Update Checks <<<

    # Check if Celestrak page has been updated
    update_celestrak, last_update_celestrak = celestrak_update_check(metadata, False)
    print(" Celestrak Data last updated: ", last_update_celestrak, ". Update required: ", update_celestrak)

    # Check if Celestrak page has been updated
    update_ucs, last_update_ucs = ucs_update_check(metadata)
    print(" UCS Data last updated: ", last_update_ucs, ". Update required: ", update_ucs)
    if commit_data and (update_celestrak):
        add_files = "git add ./dat/meta/last_data_update.csv"
        os.system(add_files)
        os.system('git commit -m "metadata file updated for satellite catalogue data"')                
    
    # >>> Import/Export Data <<<

    # Override metadata checks
    if update_satcat:
        update_celestrak =  True; update_ucs =  True

    if update_celestrak or update_ucs:
        # Celestrak data import
        celestrak_dat = import_celestrak_satcat(filename_celestrak, update_celestrak)
        # UCS data import
        ucs_dat = import_ucs_satcat(filename_ucs, update_ucs)
        # Merge datasets and export to csv
        satcat_shape, satcat_cols = clean_satcat_export(celestrak_dat, ucs_dat, filename_satcat)
        print("Satellite catalogue contains ", satcat_shape[0], " rows and ",
              satcat_shape[1], " columns")
        print("Columns in Satellite catalogue:", satcat_cols)
        # Update SQL database
        satcat_sql_dump(filename_satcat,  satdat_dbs)

        if commit_data:
            files = [filename_celestrak, filename_ucs, filename_satcat, satdat_dbs]
            add_files = "git add ./dat/clean/" + " ./dat/clean/".join(files[update_celestrak, update_ucs, True, True])
            os.system(add_files)
            os.system('git commit -m "Satellite catalogue updated"')    
                    

def tle_pipeline(metadata,
                 update_tle_override,                 
                 satdat_dbs,
                 filename_satcat_tle,
                 commit_data):
    ''' 
    Run TLE data pipeline.

    @param metadata: (str) filename of download metadata
    @param update_tle_override: (boolean) If true, update TLE data (override)    
    @param satdat_dbs: (str) name of sqlite database to write in TLE data
    @param tle_format: (str) Format of GP elements - currently only accepts "tle"
    @param filename_satcat_tle: (str) name of csv file to write in merged satellite catalogue and TLE data
    @param commit_data: (boolean) If True, commit updated satellite catalogue data to github    
    '''        
    
    
    # >>> Page Update Checks <<<
    
    # Check if Celestrak page has been updated
    update_tle, last_update_tle = celestrak_update_check(metadata, True)
    print(" Celestrak TLE Data last updated: ", last_update_tle, ". Update required: ", update_tle) 
    if commit_data and update_tle:
        add_files = "git add ./dat/meta/last_data_update.csv"
        os.system(add_files)
        os.system('git commit -m "metadata file updated for TLE data"')                
    
    # >>> Import/Export Data <<<

    if update_tle or update_tle_override:
        missing_satcat_ids, num_downloaded  = extract_TLE_active(satdat_dbs, last_update_tle)
        print("TLEs downloaded for ",num_downloaded," active satellites")
        satcat_no_data = extract_TLE(satdat_dbs, last_update_tle, missing_satcat_ids)
        print("TLEs could not be found for ",len(satcat_no_data), "/",
              num_downloaded+len(missing_satcat_ids)," satellites")
        export_satcat_tle(satdat_dbs, filename_satcat_tle)  
        
        if commit_data:
            files = [satdat_dbs, filename_satcat_tle]
            add_files = "git add ./dat/clean/" + " ./dat/clean/".join(files)
            os.system(add_files)
            os.system('git commit -m "TLE data updated"')          

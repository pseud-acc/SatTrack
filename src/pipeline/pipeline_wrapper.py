#!/usr/bin/env python

"""

This module contains wrapper functions for the satellite catalogue, webscraper and TLE data pipeline functions.

Example:

        $ python pipeline_wrapper.py

Attributes: 

Todo:
    * 

"""

import sys
sys.path.append("../../")

# satcat creation
from src.pipeline.satcat_creation.celestrak_import import celestrak_update_check, import_celestrak_satcat
from src.pipeline.satcat_creation.ucs_import import ucs_update_check, import_ucs_satcat
from src.pipeline.satcat_creation.create_satcat import clean_satcat_export, satcat_sql_dump
# satcat enrichment
from src.pipeline.satcat_enrichment.skyrocket_webscraper import skyrocket_update_check, webscraper_dump, enrich_satcat
# tle import
from src.pipeline.tle_import.extract_TLEs import extract_TLE_active, extract_TLE, remove_decayed_TLE, drop_staging_tables
# app data export
from src.pipeline.app_data_export.export_app_data import export_satcat_tle

def satcat_pipeline(metadata,
                    update_satcat,
                    filename_celestrak,
                    filename_ucs,
                    filename_satcat,
                    satdat_dbs):
    
    ''' 
    Run satellite catalogue pipeline.

    @param metadata_location: (str) filename of download metadata
    @param update_satcat: (boolean) If true, update satellite catalogue data (override)
    @param filename_celestrak: (str) name of csv file to write in clean CelesTrak data
    @param filename_ucs: (str) name of csv file to write in clean UCS data 
    @param filename_satcat: (str) name of csv file to write in clean merged satellite catalogue data 
    @param satdat_dbs: (str) name of sqlite database to write in merged satallite catalogue data     
    '''    
    
    print("")
    print("===========================")
    print("Satellite catalogue pipeline - Extract Celestrak & UCS data")
    print("===========================")    
    print("")           
    
    # >>> Page Update Checks <<<

    # Check if Celestrak page has been updated
    update_celestrak, last_update_celestrak = celestrak_update_check(metadata, False)
    print(" Celestrak Data last updated: ", last_update_celestrak, ". Update required: ", update_celestrak)

    # Check if UCS page has been updated
    update_ucs, last_update_ucs = ucs_update_check(metadata)
    print(" UCS Data last updated: ", last_update_ucs, ". Update required: ", update_ucs)
    
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
        
def satcat_enrichement_pipeline(metadata,
                                full_update_check,
                                webscraper_override,
                                satdat_dbs,
                                filename_enriched_satcat):
    ''' 
    Run webscraper on skyrocket website and enrich existing satellite catalogue data.

    @param webscraper_override: (boolean) If true, run webscraper (override)    
    @param satdat_dbs: (str) name of sqlite database to write in webscraped data
    @param filename_enriched_satcat: (str) name of csv file to write in enriched satellite catalogue data     
    '''      
    
    print("")
    print("===========================")
    print("Webscraper pipeline - satellite catalogue enrichment")
    print("===========================")    
    print("")       
    
    # Check if Skyrocket page(s) has been updated
    update_skyrocket, last_update_skyrocket = skyrocket_update_check(metadata, full_update_check)
    print(" Skyrocket Data last updated: ", last_update_skyrocket, ". Update required: ", update_skyrocket)    
    
    # Scrape data from skyrocket website
    if webscraper_override or update_skyrocket:
        webscraper_dump(satdat_dbs)
    
    # Enrich satellite catalogue with skyrocket data
    enrich_satcat(satdat_dbs, filename_enriched_satcat)
    
    # Update SQL database
    satcat_sql_dump(filename_enriched_satcat,  satdat_dbs)            
                    

def tle_pipeline(metadata,
                 update_tle_override,                 
                 satdat_dbs):
    ''' 
    Run TLE data pipeline.

    @param metadata: (str) filename of download metadata
    @param update_tle_override: (boolean) If true, update TLE data (override)    
    @param satdat_dbs: (str) name of sqlite database to write in TLE data
    @param tle_format: (str) Format of GP elements - currently only accepts "tle"
    @param filename_satcat_tle: (str) name of csv file to write in merged satellite catalogue and TLE data
    '''        
    
    
    # >>> Page Update Checks <<<
    
    print("")
    print("===========================")
    print("TLE pipeline - Extract Celestrak data")
    print("===========================")    
    print("")    
    
    # Check if Celestrak TLE page has been updated
    update_tle, last_update_tle = celestrak_update_check(metadata, True)
    print(" Celestrak TLE Data last updated: ", last_update_tle, ". Update required: ", update_tle) 
    
    # >>> Import/Export Data <<<

    # Remove decayed satellites from TLE database
    remove_decayed_TLE(satdat_dbs)
    print("TLEs successfully removed from database for decayed satellites")


    if update_tle or update_tle_override:
        api_request_limit_not_reached, missing_satcat_ids, num_downloaded  = extract_TLE_active(satdat_dbs, last_update_tle)
        if api_request_limit_not_reached:
            print("TLEs downloaded for ",num_downloaded," active satellites")

            print("Attempt to extract TLEs for individual satellites...")
            satcat_no_data = extract_TLE(satdat_dbs, last_update_tle, missing_satcat_ids)
            print("TLEs could not be found for ",len(satcat_no_data), "/",
                  num_downloaded+len(missing_satcat_ids)," satellites")
            # Drop TLE staging tables
            drop_staging_tables(satdat_dbs)
            print("Remove TLE staging tables from database")
        
def app_data_export(satdat_dbs,
                filename_satcat_tle):
    ''' 
    Export merged satellite catalogue and TLE data for app.

    @param satdat_dbs: (str) name of sqlite database import satellite catalogue and TLE data.
    @param filename_satcat_tle: (str) name of csv file to write in merged satellite catalogue and TLE data
    '''        
    
    print("")
    print("===========================")
    print("App data export")
    print("===========================")    
    print("")        
    
    export_satcat_tle(satdat_dbs, filename_satcat_tle)  

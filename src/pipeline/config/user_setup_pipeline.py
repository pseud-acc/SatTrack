#!/usr/bin/env python

"""

This module defines the user input parameters for the satellite catalogue, data enrichment and TLE data pipeline functions.

Example:

        $ python user_setup_pipeline.py

Attributes: 

Todo:
    * 

"""

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Define User Inputs
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#-------------------------------------#
# A. Create Satellite Catalogue 
#-------------------------------------#

satcat_params = dict(
    metadata = "./dat/meta/last_data_update.csv",
    update_satcat = True,
    filename_celestrak = "celestrak_satcat.csv",
    filename_ucs = "ucs_satcat.csv",
    filename_satcat = "merged_satcat.csv",
    satdat_dbs = "satdat.sqlite"
    )

#-------------------------------------#
# B. Satellite Catalgoue Enrichment 
#-------------------------------------#

satcat_enrichement_params = dict(
    metadata = "./dat/meta/last_data_update.csv",
    full_update_check = False,
    webscraper_override = False,    
    satdat_dbs = "satdat.sqlite",
    filename_enriched_satcat = "enriched_satcat.csv"
    )

#-------------------------------------#
# C. Extract TLE Data 
#-------------------------------------#

tle_params = dict(
    metadata = "./dat/meta/last_data_update.csv",
    update_tle_override = True,    
    satdat_dbs = "satdat.sqlite"
    )

#-------------------------------------#
# D. Export App Data
#-------------------------------------#

export_app_data_params = dict(
    satdat_dbs = "satdat.sqlite",
    filename_satcat_tle = "satcat_tle.csv"
    )
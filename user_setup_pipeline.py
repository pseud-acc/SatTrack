#!/usr/bin/env python

"""

This module defines the user input parameters for the satellite catalogue and TLE data pipeline functions.

Example:

        $ python user_setup_pipeline.py

Attributes: 

Todo:
    * 

"""

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Define User Inputs
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#----------------------------#
# A. Satellite Catalogue 
#----------------------------#

satcat_params = dict(
    metadata = "./dat/meta/last_data_update.csv",
    update_satcat = True,
    filename_celestrak = "celestrak_satcat.csv",
    filename_ucs = "ucs_satcat.csv",
    filename_satcat = "merged_satcat.csv",
    satdat_dbs = "satdat.sqlite"
    )

#----------------------------#
# B. TLE Data 
#----------------------------#

tle_params = dict(
    metadata = "./dat/meta/last_data_update.csv",
    update_tle_override = True,    
    satdat_dbs = "satdat.sqlite",
    filename_satcat_tle = "satcat_tle.csv"
    )


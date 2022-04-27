#!/usr/bin/env python

"""

This module runs the TLE data pipeline. In this script, satellite General perturbation Element set data is extracted from the Celestrak website and exported to a SQL database.

Example:

        $ python tle_pipeline.py

Attributes:

Todo:
    * 

"""

import sys

sys.path.append("./src/pipeline/")

from celestrak_import import celestrak_update_check
from extract_TLEs import extract_TLE_active, extract_TLE, export_satcat_tle


#----------------------------#
# USER INPUTS 
#----------------------------#

"""
Metadata location:
    If True - override last update checks and create new satellite catalogue
"""
update_satcat = True

"""
Metadata location:
    csv file containing most recent date for Celestrak and UCS website updates 
    and satellite catalogue download
"""
metadata = "dat\\meta\\last_data_update.csv"

"""
Celestrak Satellite Catalogue Page url:
    URL for Celestrak Satellite Catalogue search page
"""
url_celestrak = "https://celestrak.com/NORAD/elements/"

"""
Satellite Catalogue Database name:
    Name of SQLITE database to export satellite catalogue to in ".\dat\clean\" - saved as "satcat" table. 
"""
satcat_dbs = "satcat.sqlite"

"""
TLE Format:
    Format of GP data to extract. Only allows "tle" at present.
"""
tle_format = "tle"

"""
Extract TLEs:
    True if extracting TLEs from Celestrak. Celestrak URL must point to
    Celestrak General Perturbations (GP) Element sets website.
"""
extract_tle = True

"""
Satellite Catalogue-TLE Filename:
    Name of csv to export merged satellite catalogue and TLE data. Exported to ".\dat\clean\"
"""
filename_satcat_tle = "satcat_tle.csv"


#----------------------------#
# PAGE UPDATE CHECKS
#----------------------------#

# Check if Celestrak page has been updated
update_celestrak, last_update_celestrak = celestrak_update_check(url_celestrak, metadata, extract_tle)

print(" Celestrak TLE Data last updated: ", last_update_celestrak)

#----------------------------#
# IMPORT/EXPORT DATA
#----------------------------#

if update_celestrak or update_satcat:
    missing_satcat_ids, num_downloaded  = extract_TLE_active(satcat_dbs, tle_format, last_update_celestrak)
    print("TLEs downloaded for ",num_downloaded," active satellites")
    satcat_no_data = extract_TLE(satcat_dbs, tle_format, last_update_celestrak, missing_satcat_ids)
    print("TLEs could not be found for ",len(satcat_no_data), "/",
          num_downloaded+len(missing_satcat_ids)," satellites")
    export_satcat_tle(satcat_dbs, filename_satcat_tle)
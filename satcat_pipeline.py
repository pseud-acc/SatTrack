#!/usr/bin/env python

"""

This module runs the SatTrak data pipeline. In this script, satellite data is extracted from the CelesTrak and UCS satellite catalogues, cleaned, merged and exported to a SQL database.

Example:

        $ python satcat_pipeline.py

Attributes:
    module_level_variable1 (int): 

Todo:
    * 

"""

import sys

sys.path.append("./src/")

from celestrak_import import celestrak_update_check, import_celestrak_satcat
from ucs_import import ucs_update_check, import_ucs_satcat
from create_satcat import clean_satcat_export, satcat_sql_dump

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
url_celestrak = "https://celestrak.com/satcat/search.php"


"""
Celestrak Satellite Catalogue csv url:
    URL for Celestrak Satellite Catalogue csv
"""
url_celestrak_csv = "https://celestrak.com/pub/satcat.csv"


"""
Celestrak Owner description url:
    URL for Celestrak page containing table with owner code descriptions
"""
url_celestrak_owner = "https://celestrak.com/satcat/sources.php"

"""
Celestrak Owner description url:
    URL for Celestrak page containing table with launchsite code descriptions
"""
url_celestrak_launchsite = "https://celestrak.com/satcat/launchsites.php"


"""
Extract TLEs:
    True if extracting TLEs from Celestrak. Celestrak URL must point to
    Celestrak General Perturbations (GP) Element sets website.
"""
extract_tle = False

"""
Celestrak Filename:
    Name of csv file to import/export Celestrak satellite catalogue data. Located in ".dat\clean\"
"""
filename_celestrak = "celestrak_satcat.csv"

"""
UCS Satellite Catalogue url:
    URL for UCS Satellite database page
"""
url_ucs = "https://www.ucsusa.org/resources/satellite-database"

"""
UCS Filename:
    Name of csv file to import/export clean UCS satellite catalogue data. Imported from ".\dat\clean\"
"""
filename_ucs = "ucs_satcat.csv"

"""
Satellite Catalogue Filename:
    Name of csv to export merged (Celestrak and UCS) satellite catalogue data. Exported to ".\dat\clean\"
"""
filename_satcat = "clean_satcat.csv"

"""
Satellite Catalogue Database name:
    Name of SQLITE database to export satellite catalogue to in ".\dat\clean\" - saved as "satcat" table. 
"""
satcat_dbs = "satcat.sqlite"

#----------------------------#
# PAGE UPDATE CHECKS
#----------------------------#

# Check if Celestrak page has been updated
update_celestrak, last_update_celestrak = celestrak_update_check(url_celestrak, metadata, extract_tle)

print(" Celestrak Data last updated: ", last_update_celestrak)

# Check if Celestrak page has been updated
update_ucs, last_update_ucs = ucs_update_check(url_ucs, metadata)

print(" UCS Data last updated: ", last_update_ucs)

print(update_ucs, update_celestrak)

#----------------------------#
# IMPORT/EXPORT DATA
#----------------------------#

# Override metadata checks
if update_satcat:
    update_celestrak =  True; update_ucs =  True

if update_celestrak or update_ucs:
    # Celestrak data import
    celestrak_dat = import_celestrak_satcat(url_celestrak_csv, url_celestrak_owner, url_celestrak_launchsite,
                                            filename_celestrak, update_celestrak)
    # UCS data import
    ucs_dat = import_ucs_satcat(url_ucs, filename_ucs, update_ucs)
    # Merge datasets and export to csv
    satcat_shape, satcat_cols = clean_satcat_export(celestrak_dat, ucs_dat, filename_satcat)
    print("Satellite catalogue contains ", satcat_shape[0], " rows and ",
          satcat_shape[1], " columns")
    print("Columns in Satellite catalogue:", satcat_cols)
    # Update SQL database
    satcat_sql_dump(filename_satcat,  satcat_dbs)

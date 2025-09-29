#!/usr/bin/env python

"""

This module defines user

Example:

        $ python user_setup_app.py

Attributes:

Todo:
    *

"""

## >>>>>>>> Setup App Inputs <<<<<<<<<<<<

"""
    App Data Locations
"""
#satcat_loc = "./dat/clean/satcat_tle.csv"
satcat_loc = "https://raw.githubusercontent.com/pseud-acc/SatTrack/refs/heads/main/dat/clean/satcat_tle.csv"
img_loc = "./assets/images/gray_scale_earth_2048_1024.jpg"
metadata_loc = "./dat/meta/last_data_update.csv"

"""
    Greyscale Earth Map Resolution
"""
resolution = 8
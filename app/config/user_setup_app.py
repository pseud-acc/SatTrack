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
# Satellite data comes from the pipeline's app files: S3 (SATTRACK_S3_BUCKET) or a local folder
# (SATTRACK_APP_DATA_DIR); see app/core/state.py.
img_loc = "./assets/images/gray_scale_earth_2048_1024.jpg"

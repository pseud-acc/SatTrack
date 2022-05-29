#!/usr/bin/env python

"""

This module runs the satellite catalogue and TLE data pipelines.

Example:

        $ python run_pipeline_manual.py

Attributes: 

Todo:
    * 

"""

import sys

sys.path.append("./src/pipeline/")

from user_setup_pipeline import *
from pipeline_wrapper import satcat_pipeline, tle_pipeline


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Run Satellite Catalogue Pipeline
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

satcat_pipeline(**satcat_params)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Run TLE Data Pipeline
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

tle_pipeline(**tle_params)
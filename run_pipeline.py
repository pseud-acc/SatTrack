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
sys.path.append("./src/pipeline/config")

from user_setup_pipeline import *
from pipeline_wrapper import satcat_pipeline, tle_pipeline, satcat_enrichement_pipeline, app_data_export


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Run Satellite Catalogue Pipeline
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

satcat_pipeline(**satcat_params)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Run Satellite Catalogue Enrichment Pipeline
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#satcat_enrichement_pipeline(**satcat_enrichement_params)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Run TLE Data Pipeline
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

tle_pipeline(**tle_params)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Export App Data
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

app_data_export(**export_app_data_params)
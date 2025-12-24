#!/usr/bin/env python

"""

This module defines functions to assist with filter display

Example:

        $ python helper__filter_display.py

Function:
    year_slider_display_output: Create display output for year slider
Todo:
    *

"""

import numpy as np
from dash import html

def sort_filter_dropdown_options(df):
    '''
    Format dynamic filter options for dropdowns.
    @param df: (DataFrame) Satellite dataframe
    @return: (dict) Formatted dynamic filter options
    '''
    # Generate filter options
    filter_output = list(np.sort(df.ObjectName.unique())), list(
            np.sort(df.SatCatId.unique()).astype(str))

    return filter_output

def format_year_slider_output(range_type, year):
    '''
    :param range_type: str
    :param year: int
    :return: list
    '''
    return [
        html.Strong(f"{range_type}: "),
        f"{str(year)}"
    ]
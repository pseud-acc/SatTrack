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

SEARCH_LIMIT = 50   # options returned per search: enough to pick from, small enough for the browser to index at once


def search_options(df, name_search, id_search, satname=None, satcatid=None, limit=SEARCH_LIMIT):
    """Options for the two search dropdowns, from what is typed in them (server-side search).

    Dash 4's dcc.Dropdown builds a full-text index of every option in the browser; with ~16,000 names and ~16,000
    SATCAT numbers that blocked the page for over 2 s on load. So the dropdowns start empty and offer at most `limit`
    matches among the satellites `df` (already filtered by the sidebar) holds:
    - names: case-insensitive; names starting with the text first, then names containing it, each alphabetical;
    - SATCAT numbers: numbers starting with the typed digits, in numeric order.
    The current selection is always among its dropdown's options, so the dropdown can display it.
    @return: (name options, SATCAT options), lists of str
    """
    names = []
    text = (name_search or "").strip().casefold()
    if text:
        unique = sorted(df.ObjectName.dropna().unique())
        starts = [n for n in unique if n.casefold().startswith(text)]
        contains = [n for n in unique if text in n.casefold() and not n.casefold().startswith(text)]
        names = (starts + contains)[:limit]
    ids = []
    digits = (id_search or "").strip()
    if digits.isdigit():
        all_ids = np.sort(df.SatCatId.unique()).astype(str)
        ids = [i for i in all_ids if i.startswith(digits)][:limit]
    if satname and satname not in names:
        names.insert(0, satname)
    if satcatid and str(satcatid) not in ids:
        ids.insert(0, str(satcatid))
    return names, ids


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
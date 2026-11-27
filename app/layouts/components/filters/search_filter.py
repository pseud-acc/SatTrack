"""
Satellite search (D-052; roadmap 3.9's browsable list, built early).

A list you can scroll (space stations first, then the newest launches) and narrow by typing a name or a SATCAT number.
It is drawn in the browser by assets/07_search.js from /data/search.json (app/core/search_index.py), so the page
no longer carries ~40,000 dropdown options (owner, 27 Nov 2026: 5 s of main-thread time on a slowed phone CPU).
Picking a satellite sets the hidden `satcatid-filter-dropdown` value, which the panel's callbacks read like any other
control; picking it again, its chip's x, or Clear all removes it. `satname-filter-dropdown` stays as a hidden value
(the filter spec still supports a name), set by nothing in the page today. Both ids are kept from the dropdowns they
replace, so the panel callbacks, chips and tests are unchanged.
"""

from dash import dcc, html


def create_search_filter():
    """
    Returns:
        html.Div: the search box and list (filled in the browser) and the two hidden values
    """
    return html.Div([
        html.Label("Search satellite", className="st-lbl", htmlFor="sat-search-input"),
        html.Div(id="sat-search", className="st-search mb-3", **{"data-src": "/data/search.json"}),
        dcc.Input(id="satname-filter-dropdown", type="hidden", value=None),
        dcc.Input(id="satcatid-filter-dropdown", type="hidden", value=None),
    ])

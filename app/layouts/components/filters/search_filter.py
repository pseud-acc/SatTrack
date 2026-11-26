"""
Satellite search filter component (by name and SATCAT ID).
"""

from dash import dcc, html


def create_search_filter(options):
    """
    Create the satellite search filter component.

    Args:
        options (dict): Dictionary containing satname and satcatid options

    Returns:
        html.Div: Search filter component
    """
    return html.Div([
        html.Label("Search Satellite", className="st-lbl"),
        dcc.Dropdown(
            options=options["satname"],
            placeholder="Type to search...",
            id="satname-filter-dropdown",
            className="mb-2 st-adv-dropdown"
        ),
        dcc.Dropdown(
            options=options["satcatid"],
            placeholder="SATCAT Number",
            id="satcatid-filter-dropdown",
            className="mb-3 st-adv-dropdown"
        )
    ])

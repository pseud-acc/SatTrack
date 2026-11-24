"""
Satellite search filter component (by name and SATCAT ID).
"""

from dash import dcc, html


def create_search_filter(options):
    """
    Create the satellite search filter component.

    Args:
        options (dict): Dictionary of filter options (unused here: the search dropdowns start empty and get their
            options from what is typed, app/callbacks/callback_filters.py, because Dash 4's Dropdown indexes every
            option in the browser)

    Returns:
        html.Div: Search filter component
    """
    return html.Div([
        html.Label("Search Satellite", className="fw-bold small"),
        dcc.Dropdown(
            options=[],
            placeholder="Type a satellite name...",
            id="satname-filter-dropdown",
            className="mb-2",
            style={'fontSize': '0.875rem'}
        ),
        dcc.Dropdown(
            options=[],
            placeholder="Type a SATCAT number...",
            id="satcatid-filter-dropdown",
            className="mb-3",
            style={'fontSize': '0.875rem'}
        )
    ])

"""
Filter sidebar orchestrator component.
Combines all filter components into a cohesive sidebar.
"""

from dash import html
import dash_bootstrap_components as dbc
from app.layouts.components.filters.status_filter import create_status_filter
from app.layouts.components.filters.orbit_filter import create_orbit_filter
from app.layouts.components.filters.search_filter import create_search_filter
from app.layouts.components.filters.advanced_filters import create_advanced_filters


def create_filter_sidebar(options):
    """
    Create the complete filter sidebar with all filter components.

    Args:
        options (dict): Dictionary containing all filter options

    Returns:
        dbc.Col: Filter sidebar column component
    """
    return dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.H5("Filters", className="mb-0 d-inline-block"),
                dbc.Button(
                    html.I(className="fas fa-chevron-down"),
                    id="toggle-filters",
                    color="link",
                    className="float-end d-md-none p-0"
                )
            ]),
            dbc.Collapse([
                dbc.CardBody([
                    # Status Filter
                    create_status_filter(),

                    # Orbit Filter
                    create_orbit_filter(options),

                    # Satellite Search
                    create_search_filter(options),

                    # Advanced Filters (collapsible)
                    create_advanced_filters(options),

                    # Action Buttons
                    dbc.ButtonGroup([
                        dbc.Button("Update", id="time-update-btn", color="primary", size="sm"),
                        dbc.Button("Clear Orbits", id="clear-orbits-btn", color="secondary", size="sm")
                    ], className="w-100")
                ])
            ], id="filter-collapse", is_open=False, className="")
        ], className="mb-3 shadow-sm")
    ], xs=12, md=4, lg=3)

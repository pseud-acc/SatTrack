"""
Filter sidebar orchestrator component.
Combines all filter components into a cohesive sidebar.
"""

from dash import html
import dash_bootstrap_components as dbc
from app.layouts.components.filters.type_filter import create_type_filter
from app.layouts.components.filters.status_filter import create_status_filter
from app.layouts.components.filters.orbit_filter import create_orbit_filter
from app.layouts.components.filters.search_filter import create_search_filter
from app.layouts.components.filters.advanced_filters import create_advanced_filters
from app.core.viewer import viewer_state


def create_filter_sidebar(options, type_totals=None):
    """
    Create the complete filter sidebar with all filter components.

    Args:
        options (dict): Dictionary containing all filter options
        type_totals (dict): object type -> count in the objects dataset (the type switches show it)

    Returns:
        dbc.Col: Filter sidebar column component
    """
    return dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.H2("Filters", className="st-panel-title"),
                # Phones: show or hide the filters under the bar
                dbc.Button(
                    html.I(className="st-icon st-icon-chevron-down", id="toggle-icon"),
                    id="toggle-filters",
                    color="link",
                    className="st-panel-btn d-md-none",
                    title="Show or hide the filters"
                ),
                # Desktop: fold the panel to a thin strip so the views get the width (3.12 step 3)
                dbc.Button(
                    html.I(className="st-icon st-icon-chevron-left", id="panel-strip-icon"),
                    id="panel-strip-toggle",
                    color="link",
                    className="st-panel-btn d-none d-md-inline-flex",
                    title="Fold the filter panel"
                ),
            ], className="st-panel-head"),
            dbc.Collapse([
                dbc.CardBody([
                    # Object types (roadmap 3.3a): only with the globe on, the one view that draws rocket bodies and
                    # debris (the Plotly views draw the app CSV's payloads only)
                    create_type_filter(type_totals or {}, shown=viewer_state()["enabled"]),

                    # Status Filter
                    create_status_filter(),

                    # Orbit Filter
                    create_orbit_filter(options),

                    # Satellite Search
                    create_search_filter(options),

                    # Advanced Filters (collapsible)
                    create_advanced_filters(options),

                    # Action Buttons
                    html.Div([
                        dbc.Button("Update", id="time-update-btn", color="primary", size="sm"),
                        dbc.Button("Clear Orbits", id="clear-orbits-btn", color="secondary", outline=True, size="sm")
                    ], className="st-panel-actions")
                ])
            ], id="filter-collapse", is_open=False, className="")
        ], className="st-panel mb-3")
    ], xs=12, md=4, lg=3, className="st-panel-col")

#!/usr/bin/env python

"""
This module defines the dash app layout for satellite visualizations.

Example:
        $ python app_layout.py

Function:
    create_dash_layout: function to define dash app layout.

Todo:
    *
"""

## Packages
import sys
from dash import dcc
import dash_bootstrap_components as dbc

## Internal Modules
sys.path.append("../../")

# app data
from app.core.state import get_app_data

# Layout components
from app.layouts.components.header import create_credits
from app.layouts.components.filter_sidebar import create_filter_sidebar
from app.layouts.components.visualization_area import create_visualization_area
from app.helper.helper__app_data import sidebar_filter_spec
from app.helper.helper__filter_display import default_controls, panel_summary
from app.core import filter_spec


## --- Define Dash layout ----
def create_dash_layout(app):
    """
    Create the main Dash layout for satellite visualization page.

    Args:
        app: Dash application instance

    Returns:
        layout: Complete Dash layout
    """
    app.title = "SatTrack"

    # Get app data
    app_data = get_app_data()
    tbl_col_map = app_data['data']['tbl_col_map']
    fig2d_0 = app_data['viz_2d']['base_figure']
    fig3d_0 = app_data['viz_3d']['base_figure']    
    options = app_data['filter']['options']
    filter_table = app_data['filter']['table']
    # The spec the page opens with (roadmap 3.3a): rendered into the store, so the globe masks before its first
    # positions with no round trip (D-042) and every view starts from the same spec. The panel's count, type counts,
    # chips and row summaries for the same values are rendered too (3.3b), so nothing runs at load.
    start = default_controls()
    start_spec = filter_spec.validate(sidebar_filter_spec(**start))
    summary = panel_summary(filter_table, start)

    layout = dbc.Container([
        # Hidden store for viewport tracking
        dcc.Store(id='viewport-width', storage_type='session'),

        # Interval components
        dcc.Interval(id='3d-viz-interval-component', interval=20000, n_intervals=0),
        dcc.Interval(id='2d-viz-interval-component', interval=3000, n_intervals=0),

        # Memory stores
        dcc.Store(id='3d-orbit-memory', data=[]),
        dcc.Store(id='camera-memory', data=fig3d_0["layout"]["scene"]["camera"]),
        dcc.Store(id='3d-sat-ids', data=None),  # fingerprint of the satellites drawn in 3D (timer ticks patch only when unchanged)

        # The filter spec (D-031) every view reads: the globe, Plotly 3D and 2D and the list (roadmap 3.3a, Q7)
        dcc.Store(id='filter-spec', data=start_spec),

        # Main Content Area: the filter panel and the views fill the window under the top bar (D-044)
        dbc.Row([
            # Filters Sidebar - Collapsible on mobile
            create_filter_sidebar(options, summary, start),

            # Visualization Area
            create_visualization_area(fig3d_0, fig2d_0, tbl_col_map)
        ], id="tracker-row", className="g-2 g-md-3 st-tracker-row"),

        # Data credits and the conjunction caution, under the views
        create_credits(),

    ], fluid=True, className="st-tracker px-2 px-md-3 pt-2 pt-md-3")

    return layout

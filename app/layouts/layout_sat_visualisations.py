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
from app.layouts.components.header import create_header
from app.layouts.components.filter_sidebar import create_filter_sidebar
from app.layouts.components.visualization_area import create_visualization_area


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
    tle_metadata = app_data['data']['tle_metadata']
    tbl_col_map = app_data['data']['tbl_col_map']
    fig2d_0 = app_data['viz_2d']['base_figure']
    fig3d_0 = app_data['viz_3d']['base_figure']    
    options = app_data['filter']['options']

    layout = dbc.Container([
        # Hidden store for viewport tracking
        dcc.Store(id='viewport-width', storage_type='session'),

        # Interval components
        dcc.Interval(id='3d-viz-interval-component', interval=20000, n_intervals=0),
        dcc.Interval(id='2d-viz-interval-component', interval=3000, n_intervals=0),

        # Memory stores
        dcc.Store(id='3d-orbit-memory', data=[]),
        dcc.Store(id='camera-memory', data=fig3d_0["layout"]["scene"]["camera"]),

        # Header Section - Mobile Optimized
        create_header(tle_metadata),

        # Main Content Area
        dbc.Row([
            # Filters Sidebar - Collapsible on mobile
            create_filter_sidebar(options),

            # Visualization Area
            create_visualization_area(fig3d_0, fig2d_0, tbl_col_map)
        ]),

    ], fluid=True, className="px-2 px-md-3 py-3")

    return layout

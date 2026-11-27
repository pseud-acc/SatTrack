"""
Visualization area orchestrator component.
Combines all visualization tabs into a cohesive display area.
"""

import dash_bootstrap_components as dbc
from app.layouts.components.visualizations.viz_2d import create_2d_tab
from app.layouts.components.visualizations.viz_table import create_table_tab
from app.layouts.components.visualizations.viz_globe import create_globe_tab
from app.core.viewer import viewer_config, viewer_state


def create_visualization_area():
    """
    Create the complete visualization area with all visualization tabs.

    Returns:
        dbc.Col: Visualization area column component

    The globe opens by default (D-052; the Plotly 3D view was removed). The 2D and list tabs build their contents
    only when opened (callback_tabs). With the viewer switched off (SATTRACK_CESIUM_VIEWER=0, or no vendor files)
    the tracker opens on the list.
    """
    viewer = viewer_state()
    globe = [create_globe_tab(viewer_config(viewer["manifest"]))] if viewer["enabled"] else []
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Tabs(globe + [create_2d_tab(), create_table_tab()],
                         id="sat-viz-tabs", active_tab="globe" if globe else "tbl-viz", className="st-viz-tabs")
            ], className="p-2 p-md-3")
        ], className="shadow-sm")
    ], xs=12, md=8, lg=9, className="st-viz-col")

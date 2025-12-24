"""
Visualization area orchestrator component.
Combines all visualization tabs into a cohesive display area.
"""

import dash_bootstrap_components as dbc
from app.layouts.components.visualizations.viz_3d import create_3d_tab
from app.layouts.components.visualizations.viz_2d import create_2d_tab
from app.layouts.components.visualizations.viz_table import create_table_tab


def create_visualization_area(fig3d_0, fig2d_0, tbl_col_map):
    """
    Create the complete visualization area with all visualization tabs.

    Args:
        fig3d_0: Initial 3D plotly figure
        fig2d_0: Initial 2D plotly figure
        tbl_col_map: Column mapping for the satellite data table

    Returns:
        dbc.Col: Visualization area column component
    """
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                dbc.Tabs([
                    # 3D Visualization Tab
                    create_3d_tab(fig3d_0),

                    # 2D Tracker Tab
                    create_2d_tab(fig2d_0),

                    # List Tab with Mobile-Optimized Table
                    create_table_tab(tbl_col_map)

                ], id="sat-viz-tabs", active_tab="3d-viz", className="nav-fill")
            ], className="p-2 p-md-3")
        ], className="shadow-sm")
    ], xs=12, md=8, lg=9)

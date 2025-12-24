"""
Satellite list table tab component.
"""

from dash import dash_table
import dash_bootstrap_components as dbc


def create_table_tab(tbl_col_map):
    """
    Create the satellite list table tab content.

    Args:
        tbl_col_map: Column mapping for the satellite data table

    Returns:
        dbc.Tab: Table visualization tab
    """
    return dbc.Tab([
        dash_table.DataTable(
            id="satellite-list",
            columns=[
                {"name": col, "id": col, "hideable": True}
                for col in tbl_col_map.values()
            ],
            style_cell={
                'textAlign': 'center',
                'backgroundColor': '#1a1d21',
                'color': '#f8f9fa',
                'fontSize': '0.75rem',
                'padding': '8px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': '#0d0f12',
                'fontWeight': 'bold',
                'fontSize': '0.8rem'
            },
            style_table={
                'overflowX': 'auto',
                'height': 'calc(70vh - 100px)',
                'minHeight': '400px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#212529'
                }
            ],
            page_size=20,
            sort_action="native",
            export_format="csv",
            hidden_columns=['Datetime (UTC)', 'Altitude (km)'] if True else []
        )
    ], label="List View", tab_id="tbl-viz",
        label_style={"fontSize": "0.875rem", "padding": "0.5rem"})

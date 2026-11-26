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
                'backgroundColor': 'var(--st-panel)',    # design tokens (assets/03_tokens.css)
                'color': 'var(--st-fg)',
                'borderColor': 'var(--st-line)',
                'fontFamily': 'var(--st-font)',
                'fontSize': 'var(--st-fs-xs)',
                'padding': '8px',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_header={
                'backgroundColor': 'var(--st-bar)',
                'color': 'var(--st-muted)',
                'fontWeight': '600',
                'fontSize': 'var(--st-fs-xs)'
            },
            style_table={
                'overflowX': 'auto',
                'height': 'var(--st-viz-h)',   # fills the window under the top bar (assets/04_shell.css)
                'minHeight': '400px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'var(--st-raised)'
                }
            ],
            page_size=20,
            sort_action="native",
            export_format="csv",
            hidden_columns=['Datetime (UTC)', 'Altitude (km)'] if True else []
        )
    ], label="List View", tab_id="tbl-viz")

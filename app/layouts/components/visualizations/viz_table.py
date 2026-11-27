"""
Satellite list table tab component.
"""

from dash import dash_table, html
import dash_bootstrap_components as dbc


def create_table_tab():
    """The list tab with an empty body: the table is built the first time the tab is opened (callback_tabs, D-052)
    and kept; it is rebuilt only when the filters changed since it was last shown."""
    return dbc.Tab(html.Div(id="tab-list-body"), label="List View", tab_id="tbl-viz")


def create_table_body(tbl_col_map, data):
    """
    The list tab's table, built when the tab is first opened.

    Args:
        tbl_col_map: Column mapping for the satellite data table
        data: the rows for the current filters

    Returns:
        list: the table
    """
    return [
        dash_table.DataTable(
            id="satellite-list",
            data=data,
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
    ]

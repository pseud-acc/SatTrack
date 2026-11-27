"""
2D ground track visualization tab component.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_2d_tab():
    """The 2D tab with an empty body: the map is built only while the tab is open (callback_tabs, D-052), so a
    closed tab holds no map, no WebGL context and no timer, and Plotly's script loads only when it's first opened."""
    return dbc.Tab(html.Div(id="tab-2d-body"), label="2D View", tab_id="2d-viz")


def create_2d_body(fig2d):
    """The 2D tab's contents, built when the tab is opened.

    Args:
        fig2d: the 2D figure for the current filters

    Returns:
        list: the map and its hint
    """
    return [
        html.Div([
            dcc.Graph(
                id="2d-earth-satellite-plot",
                figure=fig2d,
                config={
                    'displayModeBar': False,
                    'responsive': True,
                    'scrollZoom': True,
                    'doubleClick': 'reset'
                },
                style={'height': '50vh', 'minHeight': '280px', 'maxHeight': '480px', 'width': '100%'}
            ),
        ], style={'maxWidth': '500px', 'margin': '0 auto'}),   # one world copy at mapbox zoom 0; 3.6 retires this view
        dbc.Alert(
            "Select a single satellite to see its ground track",
            color="info",
            className="mt-2 mb-0 text-center small"
        )
    ]

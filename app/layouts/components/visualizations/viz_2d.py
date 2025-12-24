"""
2D ground track visualization tab component.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_2d_tab(fig2d_0):
    """
    Create the 2D ground track visualization tab content.

    Args:
        fig2d_0: Initial 2D plotly figure

    Returns:
        dbc.Tab: 2D visualization tab
    """
    return dbc.Tab([
        html.Div([
            dcc.Graph(
                id="2d-earth-satellite-plot",
                figure=fig2d_0,
                config={
                    'displayModeBar': False,
                    'responsive': True
                },
                style={
                    'height': '50vh',
                    'minHeight': '280px',
                    'maxHeight': '480px',
                    'width': '100%'
                }
            ),
        ], style={'maxWidth': '500px', 'margin': '0 auto'}),
        dbc.Alert(
            "Select a single satellite to see its ground track",
            color="info",
            className="mt-2 mb-0 text-center small"
        )
    ],
        label="2D View", tab_id="2d-viz",
        label_style={"fontSize": "0.875rem", "padding": "0.5rem"},
        style={'paddingTop': '5px'})

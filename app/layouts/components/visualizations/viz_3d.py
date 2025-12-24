"""
3D visualization tab component.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_3d_tab(fig3d_0):
    """
    Create the 3D visualization tab content.

    Args:
        fig3d_0: Initial 3D plotly figure

    Returns:
        dbc.Tab: 3D visualization tab
    """
    return dbc.Tab([
        dcc.Graph(
            id="3d-earth-satellite-plot",
            figure=fig3d_0,
            config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan3d', 'select3d', 'lasso3d'],
                'responsive': True,
                'scrollZoom': True,
                'doubleClick': 'reset',
                'modeBarButtonsToAdd': [],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'satellite_3d_view',
                    'height': 1080,
                    'width': 1920,
                    'scale': 2
                }
            },
            style={'height': 'calc(70vh - 100px)', 'minHeight': '400px'}
        ),
        html.Div([
            html.Strong("Tip:"), " Click on satellites to see orbital paths • "
                                 "Pinch to zoom on mobile"],
            className="small text-center mt-2"
        )
    ], label="3D View", tab_id="3d-viz",
        label_style={"fontSize": "0.875rem", "padding": "0.5rem"},
        style={'paddingTop': '5px'})

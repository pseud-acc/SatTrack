"""
Status filter component (Active/Inactive satellites).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_status_filter():
    """
    Create the status filter component (Active/Inactive).

    Returns:
        html.Div: Status filter component
    """
    return html.Div([
        html.Label([
            "Status ",
            html.I(className="st-icon st-icon-info", id="status-info-icon")
        ], className="st-lbl"),
        dbc.Tooltip([
            html.Div([
                html.Strong("Active:"), " Currently operational satellites", html.Br(),
                html.Strong("Inactive:"), " Defunct or decommissioned satellites"
            ], style={'textAlign': 'left'})
        ], target="status-info-icon", placement="right"),
        dcc.Checklist(
            options=[
                {"label": " Active", "value": "Active"},
                {"label": " Inactive", "value": "Inactive"}
            ],
            value=["Active"],
            id="status-filter-checkbox",
            className="mb-3",
            inline=True,
            inputStyle={"marginRight": "5px"},
            labelStyle={"marginRight": "15px"}
        )
    ])

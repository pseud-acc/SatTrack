"""
Status filter component (Active/Inactive satellites).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import DEFAULT_STATUS


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
            ], className="st-tip-body")
        ], target="status-info-icon", placement="right"),
        dcc.Checklist(
            options=[
                {"label": " Active", "value": "Active"},
                {"label": " Inactive", "value": "Inactive"}
            ],
            value=list(DEFAULT_STATUS),   # owner, 26 Nov 2026 (roadmap 3.3a)
            id="status-filter-checkbox",
            className="mb-3 st-status-list",
            inline=True,
            labelStyle={"marginRight": "15px"}
        )
    ])

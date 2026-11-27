"""
Status filter (roadmap 3.3b, D-044): Active / Inactive / All as one segmented control, one choice at a time.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import DEFAULT_STATUS, STATUS_CHOICES


def create_status_filter():
    """
    @return: html.Div with the segmented status control (id status-filter-checkbox, value one of STATUS_CHOICES)
    """
    return html.Div([
        html.Label([
            "Status ",
            html.I(className="st-icon st-icon-info", id="status-info-icon")
        ], className="st-lbl"),
        dbc.Tooltip([
            html.Div([
                html.Strong("Active:"), " Currently operational satellites", html.Br(),
                html.Strong("Inactive:"), " Defunct or decommissioned satellites, rocket bodies and debris"
            ], className="st-tip-body")
        ], target="status-info-icon", placement="right"),
        dcc.RadioItems(
            options=[{"label": s, "value": s} for s in STATUS_CHOICES],
            value=DEFAULT_STATUS,   # owner, 26 Nov 2026 (D-049)
            id="status-filter-checkbox",   # id kept from the checklist it replaces (tests and journeys use it)
            className="st-seg",
            inline=True,
        ),
        # The globe's colours (owner, 27 Nov 2026: the panel showed type colours the globe doesn't use)
        html.Div([
            html.Span([html.Span(className="st-swatch st-swatch-active"), "Active"], className="st-key-item"),
            html.Span([html.Span(className="st-swatch st-swatch-inactive"), "Inactive"], className="st-key-item"),
        ], id="status-key", className="st-status-key mb-3", title="Colours on the globe"),
    ])

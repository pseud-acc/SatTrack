"""
Advanced filters component (owner, launch vehicle, purpose, launch year).
"""

from datetime import datetime, timezone

from dash import dcc, html
import dash_bootstrap_components as dbc
from app.helper.helper__filter_display import format_year_slider_output


def create_advanced_filters(options):
    """
    Create the advanced filters accordion component.

    Args:
        options (dict): Dictionary containing filter options

    Returns:
        dbc.Accordion: Advanced filters component
    """
    return dbc.Accordion([
        dbc.AccordionItem([
            # Owner, launch vehicle and purpose dropdowns (styled by assets/05_panel.css: .st-adv-dropdown)
            dcc.Dropdown(
                options=options["owner"],
                multi=True,
                value=[],
                placeholder="Select owners...",
                id="owner-filter-multi-dropdown",
                className="st-adv-dropdown"
            ),
            dcc.Dropdown(
                options=options["launchvehicle"],
                multi=True,
                value=[],
                placeholder="Select launch vehicles...",
                id="launchvehicle-filter-multi-dropdown",
                className="st-adv-dropdown"
            ),
            dcc.Dropdown(
                options=options["purpose"],
                multi=True,
                value=[],
                placeholder="Select purposes...",
                id="purpose-filter-multi-dropdown",
                className="st-adv-dropdown"
            ),

            # Launch year range
            html.Div([
                html.Label("Launch Year", className="st-lbl"),

                # Fixed bounds, independent of the data: 1958 to the current year (UTC), read each
                # time the page is built, so the slider reaches this year's launches without a code
                # change. The starting value still comes from the data ([1958, 2026] on 2026-11-15).
                dcc.RangeSlider(
                    min=1958,
                    max=datetime.now(timezone.utc).year,
                    step=1,
                    value=options["launchyear"],
                    marks={},
                    allow_direct_input=False,   # Dash 4: no number boxes; the min/max bubbles show the range
                    id="launchyear-filter-slider",
                    tooltip={"placement": "top", "always_visible": False},
                    className="custom-range-slider"
                ),

                # Min/max bubbles (callback_filters updates them as the slider moves)
                html.Div([
                    html.Div(id='launch-year-min-display',
                             children=format_year_slider_output('min', options['launchyear'][0]),
                             className="st-year-bubble"),
                    html.Div(id='launch-year-max-display',
                             children=format_year_slider_output('max', options['launchyear'][1]),
                             className="st-year-bubble"),
                ], className="st-year-bubbles")
            ], className="st-adv-years")

        ], title="Advanced Filters", className="border-0")
    ], start_collapsed=True, className="mb-3")

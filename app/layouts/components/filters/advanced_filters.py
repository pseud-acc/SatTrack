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
            # Owner dropdown
            dcc.Dropdown(
                options=options["owner"],
                multi=True,
                value=[],
                placeholder="Select owners...",
                id="owner-filter-multi-dropdown",
                className="mb-3",
                style={'fontSize': '0.875rem'}
            ),
            # Launch Vehicle dropdown
            dcc.Dropdown(
                options=options["launchvehicle"],
                multi=True,
                value=[],
                placeholder="Select launch vehicles...",
                id="launchvehicle-filter-multi-dropdown",
                className="mb-3",
                style={'fontSize': '0.875rem'}
            ),
            # Purpose dropdown
            dcc.Dropdown(
                options=options["purpose"],
                multi=True,
                value=[],
                placeholder="Select purposes...",
                id="purpose-filter-multi-dropdown",
                className="mb-4",
                style={'fontSize': '0.875rem'}
            ),

            # Divider for visual separation
            html.Hr(style={'margin': '20px 0', 'borderColor': 'rgba(108, 117, 125, 0.3)'}),

            # Launch Year Range section
            html.Div([
                html.Label("Launch Year", style={
                    'fontSize': '0.9rem',
                    'fontWeight': '600',
                    'color': '#6c757d',
                    'marginTop': '-10px',
                    'marginBottom': '-10px',
                    'display': 'block',
                    'textAlign': 'center'
                }),

                # Range slider
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

                # Min/Max value bubbles
                html.Div([
                    # Minimum bubble
                    html.Div([
                        html.Div(id='launch-year-min-display',
                                 children=format_year_slider_output(
                                     'min', options['launchyear'][0]
                                 ),
                                 style={
                                     'border': '1px solid #495057',
                                     'borderRadius': '10px',
                                     'padding': '8px 16px',
                                     'fontSize': '0.8rem',
                                     'fontWeight': '500',
                                     'textAlign': 'center',
                                     'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                     'color': '#c5c7c7',
                                     'maxWidth': '200px',
                                     'width': '100%'
                                 })
                    ], style={
                        'flex': '1',
                        'display': 'flex',
                        'justifyContent': 'flex-start'
                    }),

                    # Maximum bubble
                    html.Div([
                        html.Div([
                            html.Div(id='launch-year-max-display',
                                     children=format_year_slider_output(
                                         'min', options['launchyear'][0]
                                     ),
                                     style={
                                         'border': '1px solid #495057',
                                         'borderRadius': '10px',
                                         'padding': '8px 16px',
                                         'fontSize': '0.8rem',
                                         'fontWeight': '500',
                                         'textAlign': 'center',
                                         'backgroundColor': 'rgba(255, 255, 255, 0.05)',
                                         'color': '#c5c7c7',
                                         'maxWidth': '200px',
                                         'width': '100%'
                                     })
                        ], style={
                            'flex': '1',
                            'display': 'flex',
                            'justifyContent': 'flex-end'
                        }),
                    ], style={'flex': '1', 'textAlign': 'right'})
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'gap': '20px'
                })
            ], style={'paddingTop': '5px'})

        ], title="Advanced Filters", className="border-0")
    ], start_collapsed=True, className="mb-3")

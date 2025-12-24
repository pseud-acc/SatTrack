#!/usr/bin/env python

"""

This module defines the dash app layout.

Example:

        $ python app_layout.py

Function:
    create_dash_layout: function to define dash app layout.
Todo:
    * 

"""

## Packages
import sys
import pandas as pd
from dash import dcc
from dash import html
from dash import Dash, dash_table
import dash_bootstrap_components as dbc

## Internal Modules

sys.path.append("../../")


# app data
from app.helper.initialise_app_data import (options, tbl_col_map, fig2d_0, fig3d_0, tle_update)
# app helper functions
from app.helper.initialise_app import (year_slider_display_output)
# Get styles and colours
from app.styles.styles_sat_visualisations import (colours, fontsize, _tab__style, _tabs__style)

## --- Define Dash layout ----
def create_dash_layout(app):
    app.title = "SatTrack"

    layout = dbc.Container([
        # Hidden store for viewport tracking
        dcc.Store(id='viewport-width', storage_type='session'),

        # Interval components
        dcc.Interval(id='3d-viz-interval-component', interval=20000, n_intervals=0),
        dcc.Interval(id='2d-viz-interval-component', interval=3000, n_intervals=0),

        # Memory stores
        dcc.Store(id='3d-orbit-memory', data=[]),
        dcc.Store(id='camera-memory', data=fig3d_0["layout"]["scene"]["camera"]),

        # Header Section - Mobile Optimized
        dbc.Row([
            dbc.Col([
                html.H1("Live Tracker",
                        className="text-center text-md-start mb-2",
                        style={'color': colours["ttext"], 'fontSize': 'clamp(1.5rem, 5vw, 2.5rem)'}),
                html.Div([
                    html.Span("Real-time satellite tracking powered by ", className="d-block d-md-inline"),
                    dcc.Link('CelesTrak', href='https://celestrak.com/', className="text-info"),
                    html.Span(" • Last updated: " + tle_update, className="d-block d-md-inline text-muted")
                ], className="text-center text-md-start small")
            ])
        ], className="mb-3"),

        # Main Content Area
        dbc.Row([
            # Filters Sidebar - Collapsible on mobile
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("Filters", className="mb-0 d-inline-block"),
                        dbc.Button(
                            html.I(className="fas fa-chevron-down"),
                            id="toggle-filters",
                            color="link",
                            className="float-end d-md-none p-0"
                        )
                    ]),
                    dbc.Collapse([
                        dbc.CardBody([
                            # Status Filter
                            html.Div([
                                html.Label([
                                    "Status ",
                                    html.I(className="fas fa-info-circle", id="status-info-icon",
                                           style={'fontSize': '0.8rem', 'cursor': 'pointer'})
                                ], className="fw-bold small"),
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
                            ]),

                            # Orbit Filter
                            html.Div([
                                html.Label([
                                    "Orbit Type ",
                                    html.I(className="fas fa-info-circle", id="orbit-info-icon",
                                           style={'fontSize': '0.8rem', 'cursor': 'pointer'})
                                ], className="fw-bold small"),
                                dbc.Tooltip([
                                    html.Div([
                                        html.Strong("LEO:"), " Low Earth (160-2000km)", html.Br(),
                                        html.Strong("MEO:"), " Medium (2000-35786km)", html.Br(),
                                        html.Strong("GEO:"), " Geostationary (35786km)", html.Br(),
                                        html.Strong("GSO:"), " Geosynchronous", html.Br(),
                                        html.Strong("HEO:"), " Highly Elliptical"
                                    ], style={'textAlign': 'left'})
                                ], target="orbit-info-icon", placement="right"),
                                dcc.Checklist(
                                    options=[{"label": " " + orbit, "value": orbit} for orbit in options["orbit"]],
                                    value=["LEO", "GEO"],
                                    id="orbit-filter-checkbox",
                                    className="mb-3",
                                    style={"display": "grid",
                                           "gridTemplateColumns": "repeat(auto-fit, minmax(60px, 1fr))"},
                                    inputStyle={"marginRight": "5px"}
                                )
                            ]),

                            # Satellite Search
                            html.Div([
                                html.Label("Search Satellite", className="fw-bold small"),
                                dcc.Dropdown(
                                    options=options["satname"],
                                    placeholder="Type to search...",
                                    id="satname-filter-dropdown",
                                    className="mb-2",
                                    style={'fontSize': '0.875rem'}
                                ),
                                dcc.Dropdown(
                                    options=options["satcatid"],
                                    placeholder="SATCAT Number",
                                    id="satcatid-filter-dropdown",
                                    className="mb-3",
                                    style={'fontSize': '0.875rem'}
                                )
                            ]),

                            # Advanced Filters (collapsible)
                            dbc.Accordion([
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
                                        className="mb-4",  # Extra space before slider
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
                                        dcc.RangeSlider(
                                            min=1958,
                                            max=2025,
                                            step=1,
                                            value=options["launchyear"],
                                            marks={},
                                            id="launchyear-filter-slider",
                                            tooltip={"placement": "top", "always_visible": False},
                                            className="custom-range-slider"
                                        ),

                                        # Min/Max value bubbles
                                        html.Div([
                                            # Minimum bubble
                                            html.Div([
                                                html.Div(id='launch-year-min-display',
                                                         children=year_slider_display_output(
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
                                                             children=year_slider_display_output(
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
                            ], start_collapsed=True, className="mb-3"),

                            # Action Buttons
                            dbc.ButtonGroup([
                                dbc.Button("Update", id="time-update-btn", color="primary", size="sm"),
                                dbc.Button("Clear Orbits", id="clear-orbits-btn", color="secondary", size="sm")
                            ], className="w-100")
                        ])
                    ], id="filter-collapse", is_open=False, className="")
                ], className="mb-3 shadow-sm")
            ], xs=12, md=4, lg=3),

            # Visualization Area
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Tabs([
                            # 3D Visualization Tab
                            dbc.Tab([
                                dcc.Graph(
                                    id="3d-earth-satellite-plot",
                                    figure=fig3d_0,
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan3d', 'select3d', 'lasso3d'],
                                        'responsive': True
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
                                style={'paddingTop': '5px'}),

                            # 2D Tracker Tab
                            dbc.Tab([
                                html.Div([  # Added wrapper div
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
                                            'width': '100%'  # Changed from previous version
                                        }
                                    ),
                                ], style={'maxWidth': '500px', 'margin': '0 auto'}),  # Constrain and center
                                dbc.Alert(
                                    "Select a single satellite to see its ground track",
                                    color="info",
                                    className="mt-2 mb-0 text-center small"
                                )
                            ],
                                label="2D View", tab_id="2d-viz",
                                label_style={"fontSize": "0.875rem", "padding": "0.5rem"},
                                style={'paddingTop': '5px'}),

                            # List Tab with Mobile-Optimized Table
                            dbc.Tab([
                                dash_table.DataTable(
                                    id="satellite-list",
                                    columns=[
                                        {"name": col, "id": col, "hideable": True}
                                        for col in tbl_col_map.values()
                                    ],
                                    style_cell={
                                        'textAlign': 'center',
                                        'backgroundColor': '#1a1d21',
                                        'color': '#f8f9fa',
                                        'fontSize': '0.75rem',
                                        'padding': '8px',
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                    },
                                    style_header={
                                        'backgroundColor': '#0d0f12',
                                        'fontWeight': 'bold',
                                        'fontSize': '0.8rem'
                                    },
                                    style_table={
                                        'overflowX': 'auto',
                                        'height': 'calc(70vh - 100px)',
                                        'minHeight': '400px'
                                    },
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': '#212529'
                                        }
                                    ],
                                    page_size=20,
                                    sort_action="native",
                                    export_format="csv",
                                    hidden_columns=['Datetime (UTC)', 'Altitude (km)'] if True else []  # Hide on mobile
                                )
                            ], label="List View", tab_id="tbl-viz",
                                label_style={"fontSize": "0.875rem", "padding": "0.5rem"})

                        ], id="sat-viz-tabs", active_tab="3d-viz", className="nav-fill")
                    ], className="p-2 p-md-3")
                ], className="shadow-sm")
            ], xs=12, md=8, lg=9)
        ]),

        # Launch Year Range moved to Advanced Filters accordion - removed from here
    ], fluid=True, className="px-2 px-md-3 py-3")

    return layout

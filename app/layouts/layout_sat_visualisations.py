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
from app.helper.initialise_app_data import (df, options, tbl_col_map, fig2d_0, fig3d_0, tle_update)
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
                                    dcc.Dropdown(
                                        options=options["owner"],
                                        value=[],  # ✅ ADD THIS
                                        multi=True,
                                        placeholder="Select owners...",
                                        id="owner-filter-multi-dropdown",
                                        className="mb-2",
                                        style={'fontSize': '0.875rem'}
                                    ),
                                    dcc.Dropdown(
                                        options=options["launchvehicle"],
                                        multi=True,
                                        value=[],  # ✅ ADD THIS
                                        placeholder="Select launch vehicles...",
                                        id="launchvehicle-filter-multi-dropdown",
                                        className="mb-2",
                                        style={'fontSize': '0.875rem'}
                                    ),
                                    dcc.Dropdown(
                                        options=options["purpose"],
                                        multi=True,
                                        value=[],  # ✅ ADD THIS
                                        placeholder="Select purposes...",
                                        id="purpose-filter-multi-dropdown",
                                        style={'fontSize': '0.875rem'}
                                    )
                                ], title="Advanced Filters", className="border-0")
                            ], start_collapsed=True, className="mb-3"),

                            # Action Buttons
                            dbc.ButtonGroup([
                                dbc.Button("Update", id="time-update-btn", color="primary", size="sm"),
                                dbc.Button("Clear Orbits", id="clear-orbits-btn", color="secondary", size="sm")
                            ], className="w-100")
                        ])
                    ], id="filter-collapse", is_open=False, className="d-md-block")
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
                            ], label="List", tab_id="tbl-viz",
                                label_style={"fontSize": "0.875rem", "padding": "0.5rem"})

                        ], id="sat-viz-tabs", active_tab="3d-viz", className="nav-fill")
                    ], className="p-2 p-md-3")
                ], className="shadow-sm")
            ], xs=12, md=8, lg=9)
        ]),

        # Year Range Slider - Full width with mobile optimization
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Label("Launch Year Range", className="fw-bold small"),
                        dcc.RangeSlider(
                            min=1955,
                            max=2025,
                            step=1,
                            value=options["launchyear"],
                            marks={
                                year: {'label': str(year), 'style': {'fontSize': '0.7rem'}}
                                for year in range(1955, 2030, 10)
                            },
                            id="launchyear-filter-slider",
                            tooltip={"placement": "top", "always_visible": False},
                            className="mt-2"
                        )
                    ], className="p-3")
                ], className="shadow-sm mt-3")
            ])
        ])
    ], fluid=True, className="px-2 px-md-3 py-3")

    return layout
### //// OLD SCRIPT SECTION ////

        # html.Div([
        #     # Header
        #     html.H1(children="SatTrack", style={'color': colours["ttext"]}
        #             ),
        #     html.Div(children=
        #              [html.H6(["An ", dcc.Link('Open Source', href='https://github.com/pseud-acc/SatTrack'),
        #                        " Real-time Satellite Tracking App (developed by Francis Nwobu)"],
        #                       style={'color': colours["ttext"], "display": "inline-block",
        #                           'font-size': fontsize["sub-heading"],
        #                           "marginTop": 5, "marginBottom": 5}
        #                       ),
        #               html.H6(["Data sourced from ", dcc.Link('CelesTrak', href='https://celestrak.com/'), " and ",
        #                        dcc.Link('UCS Satellite Database',
        #                                 href='https://www.ucsusa.org/resources/satellite-database'),
        #                        html.Br(), "Satellite position calculated using SGP4 propagator with", html.Br(),
        #                        "two-line mean element (TLE) sets (last updated: ", tle_update, ")"],
        #                       style={'font-style': 'italic',
        #                              'color': colours["ttext"], 'font-size': fontsize["sub-sub-heading"],
        #                              "marginTop": 5, "marginBottom": 5}
        #                       )
        #               ], style={"display": "inline-block", "width": "100%"}
        #              ),
        #     # Body - Main viz/sidebar
        #
        #     # 3d viz
        #     ## Interval check
        #     dcc.Interval(
        #         id='3d-viz-interval-component',
        #         interval=1 * 20000,  # in milliseconds
        #         n_intervals=0
        #     ),
        #     ## cached memory for plot appearance
        #     dcc.Store(
        #         id='3d-orbit-memory', data=[]
        #     ),
        #     # 2d viz
        #     ## Interval check
        #     dcc.Interval(
        #         id='2d-viz-interval-component',
        #         interval=1 * 3000,  # in milliseconds
        #         n_intervals=0
        #     ),
        #     ## cached memory for plot appearance
        #     dcc.Store(id='camera-memory', data=fig3d_0["layout"]["scene"]["camera"]
        #               ),
        #     html.Div([
        #     # Sidebars
        #     html.Div([
        #         # Checklist filters
        #         html.P('Status', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": -5}
        #                ),
        #         dcc.Checklist(["Active", "Inactive"],  # Operational Status
        #                       ["Active"],
        #                       id="status-filter-checkbox",
        #                       inline=True,
        #                       inputStyle={"margin-right": "2px", "margin-left": "6px"}
        #                       ),
        #         html.P('Orbit', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": -5}
        #                ),
        #         dcc.Checklist(options["orbit"],  # Orbital Class
        #                       ["LEO", "GEO"],
        #                       id="orbit-filter-checkbox",
        #                       inline=True,
        #                       inputStyle={"margin-right": "2px", "margin-left": "6px"}
        #                       ),
        #         # Dropdown lists
        #         html.P('Satellite Name', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}
        #                ),
        #         dcc.Dropdown(options["satname"],  # Satellite Name
        #                      None,
        #                      id="satname-filter-dropdown",
        #                      style={'backgroundColor': colours["dropdownbox"],
        #                             'font-size': fontsize["dropdown"]}
        #                      ),
        #         html.P('SATCAT Number', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}
        #                ),
        #         dcc.Dropdown(options["satcatid"],  # SATCAT Number
        #                      None,
        #                      id="satcatid-filter-dropdown",
        #                      style={'backgroundColor': colours["dropdownbox"],
        #                             'font-size': fontsize["dropdown"]}
        #                      ),
        #         html.P('Owner', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}
        #                ),
        #         dcc.Dropdown(options["owner"],  # Owner
        #                      [],
        #                      id="owner-filter-multi-dropdown",
        #                      multi=True,
        #                      style={'backgroundColor': colours["dropdownbox"],
        #                             'font-size': fontsize["dropdown"]}
        #                      ),
        #         html.P('Launch Vehicle', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}
        #                ),
        #         dcc.Dropdown(options["launchvehicle"],  # Launch Vehicle Class
        #                      [],
        #                      id="launchvehicle-filter-multi-dropdown",
        #                      multi=True,
        #                      style={'backgroundColor': colours["dropdownbox"],
        #                             'font-size': fontsize["dropdown"]}
        #                      ),
        #         html.P('Purpose', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}
        #                ),
        #         dcc.Dropdown(options["purpose"],  # Purpose
        #                      [],
        #                      id="purpose-filter-multi-dropdown",
        #                      multi=True,
        #                      style={'backgroundColor': colours["dropdownbox"],
        #                             'font-size': fontsize["dropdown"]}
        #                      ),
        #         html.Div([
        #             dbc.Button('Update Time', id='time-update-btn', n_clicks=0,
        #                        className="dash-bootstrap"
        #                        ),
        #             dbc.Button('Clear 3D Orbits', id='clear-orbits-btn', n_clicks=0,
        #                        style={"display": "inline-block", "float": "right"},
        #                        className="dash-bootstrap"
        #                        )
        #         ], style={"marginTop": 20}, className="dash-bootstrap"
        #         )
        #     ], style={"display": "inline-block", "width": "25%"}
        #     ),
        #     # Satellite viz
        #     html.Div([
        #         dbc.Tabs(
        #             id="sat-viz-tabs",
        #             active_tab="3d-viz",
        #             children=[
        #                 # 3d viz
        #                 dbc.Tab(label="3D Visualisation", tab_id="3d-viz", children=[
        #                     dcc.Graph(id="3d-earth-satellite-plot",
        #                               figure=fig3d_0)
        #                 ], style=_tab__style),
        #                 # Table viz
        #                 dbc.Tab(label="List of Satellites", tab_id="tbl-viz", children=[
        #                     dash_table.DataTable(
        #                         id="satellite-list",
        #                         data=pd.DataFrame(columns=tbl_col_map.values()).to_dict("records"),
        #                         virtualization=True,
        #                         fixed_rows={'headers': True},
        #                         #                                 filter_action="native"#,
        #                         sort_action="native",
        #                         sort_mode="multi",
        #                         style_cell={'minWidth': 95, 'width': 95, 'maxWidth': 95,
        #                                     'textAlign': 'center', 'backgroundColor': "black",
        #                                     'color': colours["btext"]},
        #                         style_table={'height': 400, 'overflowX': 'auto'},  # default is 500
        #                         style_data={'whiteSpace': 'normal', 'height': 'auto',
        #                                     'lineHeight': '15px',
        #                                     'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
        #                                     'border': '1px solid grey'},
        #                         style_header={'backgroundColor': 'black', 'color': colours["btext"],
        #                                       'fontWeight': 'bold', 'border': '1px solid grey'},
        #                         export_format="csv",
        #                     )
        #                 ], style=_tab__style),
        #                 # 2d viz - satellite tracker
        #                 dbc.Tab(label="2D Satellite Tracker", tab_id="2d-viz", children=[
        #                     dcc.Graph(id="2d-earth-satellite-plot",
        #                               figure=fig2d_0),
        #                     html.H6([
        #                         "Select a satellite using either 'Satellite Name' or 'SATCAT Number' to see the 2D tracking path"],
        #                         style={'color': colours["ttext"], "display": "inline-block",
        #                                'font-size': fontsize["sub-sub-heading"], 'font-style': 'italic',
        #                                "marginTop": 5, "marginBottom": 5})
        #                 ], style=_tab__style)
        #             ], style=_tabs__style
        #     )], style={"width": "70%", "float": "right", "display": "inline-block"}
        #     )
        #     ]),
        #     # Slider filter
        #     html.Div([
        #         html.P('Launch Year', className='fix_label',
        #                style={'color': colours["btext"], 'font-weight': 'bold',
        #                       "marginTop": 5, "marginBottom": 0}),
        #         dcc.RangeSlider(1955, 2025, 1,  # Launch Year
        #                         value=options["launchyear"],
        #                         marks={str(year): {'label': str(year), 'style': {'font-size': fontsize["dropdown"]}} for
        #                                year in range(1955, 2030, 5)},
        #                         id="launchyear-filter-slider",
        #                         tooltip={"placement": "bottom", "always_visible": True})
        #     ],
        #         style={"width": "95%", "display": "inline-block"}
        #     )
        # ], style={'width': '100%', 'padding': '20px 20px 20px 20px'}), className="dash-bootstrap")

#    return layout

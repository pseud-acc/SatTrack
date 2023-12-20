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

## Internal Scripts

sys.path.append("../../")
from app.helper.app_settings import *


## --- Define Dash layout ----

def create_dash_layout(app,
                       tle_update_in,
                       options_in,
                       fig3d_0_in,
                       fig2d_0_in,
                       tbl_col_map_in
                       ):
    '''
    Function that defines dash app layout.

    @param app: (dash app object) instantiated app object

    @return app: (dash app object) app object initialised with layout. 
    '''

    # Set browser tab title
    app.title = "SatTrack"

    # Main App Layout
    app.layout = dbc.Container(
        html.Div([
            # Header
            html.H1(children="SatTrack", style={'color': colours["ttext"]}
                    ),
            html.Div(children=
                     [html.H6(["An ", dcc.Link('Open Source', href='https://github.com/pseud-acc/SatTrack'), 
                               " Real-time Satellite Tracking App (developed by Francis Nwobu)"], 
                              style={'color': colours["ttext"], "display": "inline-block",
                                  'font-size': fontsize["sub-heading"],
                                  "marginTop": 5, "marginBottom": 5}
                              ),
                      html.H6(["Data sourced from ", dcc.Link('CelesTrak', href='https://celestrak.com/'), " and ",
                               dcc.Link('UCS Satellite Database',
                                        href='https://www.ucsusa.org/resources/satellite-database'),
                               html.Br(), "Satellite position calculated using SGP4 propagator with", html.Br(),
                               "two-line mean element (TLE) sets (last updated: ", tle_update_in, ")"],
                              style={'font-style': 'italic',
                                     'color': colours["ttext"], 'font-size': fontsize["sub-sub-heading"],
                                     "marginTop": 5, "marginBottom": 5}
                              )
                      ], style={"display": "inline-block", "width": "100%"}
                     ),
            # Body - Main viz/sidebar

            # 3d viz
            ## Interval check
            dcc.Interval(
                id='3d-viz-interval-component',
                interval=1 * 20000,  # in milliseconds
                n_intervals=0
            ),
            ## cached memory for plot appearance
            dcc.Store(
                id='3d-orbit-memory', data=[]
            ),
            # 2d viz
            ## Interval check
            dcc.Interval(
                id='2d-viz-interval-component',
                interval=1 * 3000,  # in milliseconds
                n_intervals=0
            ),
            ## cached memory for plot appearance
            dcc.Store(id='camera-memory', data=fig3d_0_in["layout"]["scene"]["camera"]
                      ),
            html.Div([
            # Sidebars
            html.Div([
                # Checklist filters
                html.P('Status', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": -5}
                       ),
                dcc.Checklist(["Active", "Inactive"],  # Operational Status
                              ["Active"],
                              id="status-filter-checkbox",
                              inline=True,
                              inputStyle={"margin-right": "2px", "margin-left": "6px"}
                              ),
                html.P('Orbit', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": -5}
                       ),
                dcc.Checklist(options_in["orbit"],  # Orbital Class
                              ["LEO", "GEO"],
                              id="orbit-filter-checkbox",
                              inline=True,
                              inputStyle={"margin-right": "2px", "margin-left": "6px"}
                              ),
                # Dropdown lists
                html.P('Satellite Name', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}
                       ),
                dcc.Dropdown(options_in["satname"],  # Satellite Name
                             None,
                             id="satname-filter-dropdown",
                             style={'backgroundColor': colours["dropdownbox"],
                                    'font-size': fontsize["dropdown"]}
                             ),
                html.P('SATCAT Number', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}
                       ),
                dcc.Dropdown(options_in["satcatid"],  # SATCAT Number
                             None,
                             id="satcatid-filter-dropdown",
                             style={'backgroundColor': colours["dropdownbox"],
                                    'font-size': fontsize["dropdown"]}
                             ),
                html.P('Owner', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}
                       ),
                dcc.Dropdown(options_in["owner"],  # Owner
                             [],
                             id="owner-filter-multi-dropdown",
                             multi=True,
                             style={'backgroundColor': colours["dropdownbox"],
                                    'font-size': fontsize["dropdown"]}
                             ),
                html.P('Launch Vehicle', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}
                       ),
                dcc.Dropdown(options_in["launchvehicle"],  # Launch Vehicle Class
                             [],
                             id="launchvehicle-filter-multi-dropdown",
                             multi=True,
                             style={'backgroundColor': colours["dropdownbox"],
                                    'font-size': fontsize["dropdown"]}
                             ),
                html.P('Purpose', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}
                       ),
                dcc.Dropdown(options_in["purpose"],  # Purpose
                             [],
                             id="purpose-filter-multi-dropdown",
                             multi=True,
                             style={'backgroundColor': colours["dropdownbox"],
                                    'font-size': fontsize["dropdown"]}
                             ),
                html.Div([
                    dbc.Button('Update Time', id='time-update-btn', n_clicks=0,
                               className="dash-bootstrap"
                               ),
                    dbc.Button('Clear 3D Orbits', id='clear-orbits-btn', n_clicks=0,
                               style={"display": "inline-block", "float": "right"},
                               className="dash-bootstrap"
                               )
                ], style={"marginTop": 20}, className="dash-bootstrap"
                )
            ], style={"display": "inline-block", "width": "25%"}
            ),
            # Satellite viz
            html.Div([
                dbc.Tabs(
                    id="sat-viz-tabs",
                    active_tab="3d-viz",
                    children=[
                        # 3d viz
                        dbc.Tab(label="3D Visualisation", tab_id="3d-viz", children=[
                            dcc.Graph(id="3d-earth-satellite-plot",
                                      figure=fig3d_0_in)
                        ], style=tab_style),
                        # Table viz
                        dbc.Tab(label="List of Satellites", tab_id="tbl-viz", children=[
                            dash_table.DataTable(
                                id="satellite-list",
                                data=pd.DataFrame(columns=tbl_col_map_in.values()).to_dict("records"),
                                virtualization=True,
                                fixed_rows={'headers': True},
                                #                                 filter_action="native"#,
                                sort_action="native",
                                sort_mode="multi",
                                style_cell={'minWidth': 95, 'width': 95, 'maxWidth': 95,
                                            'textAlign': 'center', 'backgroundColor': "black",
                                            'color': colours["btext"]},
                                style_table={'height': 400, 'overflowX': 'auto'},  # default is 500
                                style_data={'whiteSpace': 'normal', 'height': 'auto',
                                            'lineHeight': '15px',
                                            'width': '150px', 'minWidth': '150px', 'maxWidth': '150px',
                                            'border': '1px solid grey'},
                                style_header={'backgroundColor': 'black', 'color': colours["btext"],
                                              'fontWeight': 'bold', 'border': '1px solid grey'},
                                export_format="csv",
                            )
                        ], style=tab_style),
                        # 2d viz - satellite tracker
                        dbc.Tab(label="2D Satellite Tracker", tab_id="2d-viz", children=[
                            dcc.Graph(id="2d-earth-satellite-plot",
                                      figure=fig2d_0_in),
                            html.H6([
                                "Select a satellite using either 'Satellite Name' or 'SATCAT Number' to see the 2D tracking path"],
                                style={'color': colours["ttext"], "display": "inline-block",
                                       'font-size': fontsize["sub-sub-heading"], 'font-style': 'italic',
                                       "marginTop": 5, "marginBottom": 5})
                        ], style=tab_style)
                    ], style=tabs_styles
            )], style={"width": "70%", "float": "right", "display": "inline-block"}
            )
            ]),
            # Slider filter
            html.Div([
                html.P('Launch Year', className='fix_label',
                       style={'color': colours["btext"], 'font-weight': 'bold',
                              "marginTop": 5, "marginBottom": 0}),
                dcc.RangeSlider(1955, 2025, 1,  # Launch Year
                                value=options_in["launchyear"],
                                marks={str(year): {'label': str(year), 'style': {'font-size': fontsize["dropdown"]}} for
                                       year in range(1955, 2030, 5)},
                                id="launchyear-filter-slider",
                                tooltip={"placement": "bottom", "always_visible": True})
            ],
                style={"width": "95%", "display": "inline-block"}
            )
        ], style={'width': '100%', 'padding': '20px 20px 20px 20px'}), className="dash-bootstrap")

    return app

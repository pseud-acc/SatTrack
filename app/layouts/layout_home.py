# layout_home.py
from dash import html, dcc
import dash_bootstrap_components as dbc


def create_dash_layout(app):
    layout = dbc.Container([
        # Hero Section
        dbc.Row([
            dbc.Col([
                html.H1("Track Satellites in Real-Time",
                        className="display-4 fw-bold mb-3"),
                html.P(
                    "Watch thousands of satellites orbit Earth. Explore their missions, "
                    "trajectories, and real-time positions in stunning 3D.",
                    className="lead mb-4",
                    style={'fontSize': '1.25rem'}
                ),
                dbc.ButtonGroup([
                    dbc.Button("Launch Tracker",
                               id="get-started-button",
                               color="primary",
                               size="lg",
                               className="px-4"),
                    dbc.Button("Learn More",
                               color="outline-primary",
                               size="lg",
                               href="/sat_applications",
                               className="px-4")
                ], className="mb-4"),

                # Quick Stats
                dbc.Row([
                    dbc.Col([
                        html.H3("15,000+", className="text-primary mb-0"),
                        html.P("Active Satellites", className="text-muted small")
                    ], width=4),
                    dbc.Col([
                        html.H3("Live", className="text-success mb-0"),
                        html.P("Real-Time Tracking", className="text-muted small")
                    ], width=4),
                    dbc.Col([
                        html.H3("Free", className="text-info mb-0"),
                        html.P("Open Source", className="text-muted small")
                    ], width=4)
                ], className="mt-4")
            ], lg=8, className="mx-auto text-center py-5")
        ]),

        html.Hr(className="my-5"),

        # Features Grid
        html.H2("Explore Satellite Data", className="text-center mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("🌍 3D Visualization", className="card-title"),
                        html.P("Interactive globe showing satellite positions and orbital paths in real-time.",
                               className="card-text")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("🔍 Advanced Filters", className="card-title"),
                        html.P("Search by satellite name, orbit type, owner, purpose, and launch year.",
                               className="card-text")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("📡 Ground Tracks", className="card-title"),
                        html.P("See 2D ground paths and predict when satellites pass overhead.",
                               className="card-text")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=6, lg=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("📊 Data Export", className="card-title"),
                        html.P("Download satellite data tables for analysis and research projects.",
                               className="card-text")
                    ])
                ], className="h-100 border-0 shadow-sm")
            ], md=6, lg=3, className="mb-3")
        ]),

        html.Hr(className="my-5"),

        # Use Cases
        dbc.Row([
            dbc.Col([
                html.H2("Who Uses SatTrack?", className="mb-4"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Strong("Students & Educators"),
                        " - Learn about orbital mechanics and space systems"
                    ], className="border-0"),
                    dbc.ListGroupItem([
                        html.Strong("Amateur Radio Operators"),
                        " - Track communication satellites for contacts"
                    ], className="border-0"),
                    dbc.ListGroupItem([
                        html.Strong("Researchers"),
                        " - Analyze satellite deployment patterns and trends"
                    ], className="border-0"),
                    dbc.ListGroupItem([
                        html.Strong("Space Enthusiasts"),
                        " - Follow ISS, Starlink, and other spacecraft"
                    ], className="border-0")
                ], flush=True)
            ], lg=6, className="mb-4"),

            dbc.Col([
                html.H2("Data Sources", className="mb-4"),
                html.P("Powered by accurate, up-to-date information:", className="mb-3"),
                html.Ul([
                    html.Li(["TLE data from ",
                             dcc.Link("CelesTrak", href="https://celestrak.com/", className="text-info")]),
                    html.Li(["Satellite database from ",
                             dcc.Link("UCS", href="https://www.ucsusa.org/resources/satellite-database",
                                      className="text-info")]),
                    html.Li("SGP4 propagator for precise calculations"),
                    html.Li("Updated daily for accuracy")
                ], className="mb-0")
            ], lg=6)
        ])
    ], fluid=True, style={'maxWidth': '1200px', 'margin': 'auto', 'padding': '40px 20px'})

    return layout
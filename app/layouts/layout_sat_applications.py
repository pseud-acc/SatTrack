# layout_sat_applications.py
import sys
from dash import html, dcc
import dash_bootstrap_components as dbc

sys.path.append("../../")

from app.styles.styles_sat_explained import (
    _main_page__style, _section_title__style, _image__style,
    _paragraph__style, _text__style, _fact_button_collapsed__style
)
from app.content.content_buttons import fact_data


def create_dash_layout(app):
    layout = html.Div(style={**_main_page__style}, children=[

        # Header
        html.Div([
            html.H1("Satellites Explained",
                    style={**_section_title__style, 'textAlign': 'center', 'fontSize': '2.5em'}),
            html.P("Discover the history, applications, and technology behind Earth's orbital infrastructure",
                   style={'textAlign': 'center', 'color': '#a0a0a0', 'fontSize': '1.1em', 'marginBottom': '40px'})
        ]),

        # Section Navigation Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("History", className="card-title text-center"),
                        html.P("From Sputnik to modern constellations", className="card-text text-center small"),
                        dbc.Button("Explore", color="info", outline=True, size="sm",
                                   href="#history", className="w-100")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Applications", className="card-title text-center"),
                        html.P("Communications, navigation, and science", className="card-text text-center small"),
                        dbc.Button("Explore", color="success", outline=True, size="sm",
                                   href="#applications", className="w-100")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Launch Systems", className="card-title text-center"),
                        html.P("Rockets and orbital mechanics", className="card-text text-center small"),
                        dbc.Button("Explore", color="warning", outline=True, size="sm",
                                   href="#launches", className="w-100")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=3, className="mb-3"),

            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Ownership", className="card-title text-center"),
                        html.P("Who operates satellites today", className="card-text text-center small"),
                        dbc.Button("Explore", color="danger", outline=True, size="sm",
                                   href="#owners", className="w-100")
                    ])
                ], className="h-100 shadow-sm hover-card")
            ], md=3, className="mb-3")
        ], className="mb-5"),

        # Statistics Dashboard
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2("1957", className="text-info mb-0"),
                        html.P("First Satellite", className="text-muted small mb-0")
                    ], className="text-center py-3")
                ], className="shadow-sm")
            ], md=3, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2("15,000+", className="text-success mb-0"),
                        html.P("Active Today", className="text-muted small mb-0")
                    ], className="text-center py-3")
                ], className="shadow-sm")
            ], md=3, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2("100+", className="text-warning mb-0"),
                        html.P("Launches/Year", className="text-muted small mb-0")
                    ], className="text-center py-3")
                ], className="shadow-sm")
            ], md=3, className="mb-3"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2("50+", className="text-danger mb-0"),
                        html.P("Countries", className="text-muted small mb-0")
                    ], className="text-center py-3")
                ], className="shadow-sm")
            ], md=3, className="mb-3")
        ], className="mb-5"),

        # Main Content Sections
        html.Div([
            # History Section
            html.Section(id="history", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("A Brief History of Satellites", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Img(src="/assets/images/sputnik.jpg",
                                         style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                                html.P(
                                    "Sputnik 1 - The first artificial satellite, launched by the Soviet Union in 1957.",
                                    className="text-muted small mt-2",
                                    style={'textAlign': 'center', 'width': '100%'})
                            ], style={'textAlign': 'center'}),
                            dbc.Col([
                                html.P(
                                    "Satellites boast a captivating history, originating with the concept of artificial "
                                    "satellites orbiting the Earth. The notion was initially proposed by the science "
                                    "fiction writer Arthur C. Clarke in 1945. However, it wasn't until the Soviet Union's "
                                    "historic launch of Sputnik 1 on October 4, 1957, that the space age truly commenced. "
                                    "Sputnik 1, meaning 'satellite' or 'companion' in Russian, was the world's first "
                                    "artificial Earth satellite. It was a sphere with four external radio antennas, "
                                    "broadcasting radio pulses that could be received on Earth.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "This groundbreaking achievement marked the beginning of human-made objects orbiting "
                                    "our planet and kicked off the space race between the United States and the Soviet Union, "
                                    "each striving for achievements in space exploration and satellite technology.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "In the early years, satellites were primarily used for scientific research and"
                                    " national security. The United States launched the first communication satellite, Echo 1, in 1960, while the "
                                    "Soviet Union focused on scientific and reconnaissance satellites. Over time, satellites "
                                    "evolved in terms of size, usage, and ubiquity.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Today, we rely on a multitude of satellites for communication, navigation (GPS), Earth observation, "
                                    "and various scientific purposes. Satellites have become integral to our daily lives, enabling "
                                    "global connectivity and providing valuable data for scientific research and"
                                    " environmental monitoring.",
                                    style={**_paragraph__style}
                                )
                            ], md=7)
                        ]),

                        html.Hr(className="my-4"),

                        html.H5("Notable Milestones", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    fact_data["history"]["btn-1"]["button_title"],
                                    id="sat-history-btn-1",
                                    color="info",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["history"]["btn-2"]["button_title"],
                                    id="sat-history-btn-2",
                                    color="info",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["history"]["btn-3"]["button_title"],
                                    id="sat-history-btn-3",
                                    color="info",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["history"]["btn-4"]["button_title"],
                                    id="sat-history-btn-4",
                                    color="info",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2")
                        ]),

                        # Modal for expanded content
                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(id="history-modal-title")),
                            dbc.ModalBody(id="history-modal-body"),
                            dbc.ModalFooter(
                                dbc.Button("Close", id="close-history-modal", className="ms-auto")
                            )
                        ], id="history-modal", size="lg", is_open=False)
                    ])
                ], className="mb-4 shadow-sm")
            ]),

            # Applications Section
            html.Section(id="applications", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("Satellite Applications", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Img(src="/assets/images/jwst.jpg",
                                         style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                                html.P(
                                    "Modern satellites serve diverse purposes from communications to climate monitoring.",
                                    className="text-muted small mt-2",
                                    style={'textAlign': 'center', 'width': '100%'})
                            ], style={'textAlign': 'center'}),
                            dbc.Col([
                                html.P(
                                    "Satellites play a crucial role in various domains, serving purposes that extend from "
                                    "environmental monitoring to global communication. Earth observation satellites, situated "
                                    "in Low Earth Orbit (LEO), capture high-resolution images aiding in disaster response, "
                                    "climate studies, and tracking environmental changes like the effects of global warming. "
                                    "Communication satellites, typically positioned in Geostationary Orbit (GEO), facilitate "
                                    "seamless global connectivity, supporting telecommunications, broadcasting, and internet "
                                    "services.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "The choice of orbit is pivotal to a satellite's function. LEO satellites offer "
                                    "frequent revisits for real-time observation, while GEO satellites provide continuous "
                                    "coverage ideal for communication. Medium Earth Orbit (MEO) satellites, like those in "
                                    "the GPS constellation, strike a balance for navigation. High Earth Orbit (HEO) and "
                                    "polar orbits cater to specialized missions.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "The James Webb Space Telescope, positioned in a unique "
                                    "orbit, has revolutionized astronomy by making groundbreaking discoveries, including "
                                    "finding exoplanets with life-supporting molecules, massive galaxies in the infant "
                                    "universe, the earliest supermassive black holes, and complex molecules in primordial "
                                    "galaxies.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Satellite usage has dynamically evolved, notably with mega-constellations like "
                                    "Starlink and OneWeb deploying LEO satellites for global broadband internet access. "
                                    "Smaller satellites, known as CubeSats, leverage advancements in miniaturization and "
                                    "cost-effectiveness, fostering innovation in research and technology.",
                                    style={**_paragraph__style}
                                )
                            ], md=7)
                        ]),

                        html.Hr(className="my-4"),

                        html.H5("Key Applications", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    fact_data["purpose"]["btn-1"]["button_title"],
                                    id="sat-purpose-btn-1",
                                    color="success",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["purpose"]["btn-2"]["button_title"],
                                    id="sat-purpose-btn-2",
                                    color="success",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["purpose"]["btn-3"]["button_title"],
                                    id="sat-purpose-btn-3",
                                    color="success",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["purpose"]["btn-4"]["button_title"],
                                    id="sat-purpose-btn-4",
                                    color="success",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2")
                        ]),

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(id="purpose-modal-title")),
                            dbc.ModalBody(id="purpose-modal-body"),
                            dbc.ModalFooter(
                                dbc.Button("Close", id="close-purpose-modal", className="ms-auto")
                            )
                        ], id="purpose-modal", size="lg", is_open=False)
                    ])
                ], className="mb-4 shadow-sm")
            ]),

            # Launch Systems Section
            html.Section(id="launches", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("Getting to Orbit", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Img(src="/assets/images/iridium_fairing.jpg",
                                         style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                                html.P("Rocket launches deliver satellites to their designated orbits.",
                                       className="text-muted small mt-2",
                                       style={'textAlign': 'center', 'width': '100%'})
                            ], style={'textAlign': 'center'}),
                            dbc.Col([
                                html.P(
                                    "Launching a satellite demands precise planning and execution. Satellites travel to launch sites in specialized containers that shield these sensitive instruments during transport. Upon arrival, technicians perform final assembly and testing before the critical payload integration phase—where the satellite is securely fastened to the rocket's adapter. The satellite is then enclosed within the rocket's fairing, a protective aerodynamic shell that shields it from the extreme forces and temperatures encountered during ascent through the atmosphere.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Launch vehicles like SpaceX's Falcon 9 and Arianespace's Ariane 5 generate tremendous thrust to overcome Earth's gravitational pull. Engineers select rockets based on the satellite's mass and destination orbit. Communication satellites bound for Geostationary Orbit (GEO) at 35,786 km (22,236 miles) require powerful rockets with multiple stages, while Earth observation satellites destined for Low Earth Orbit (LEO) need less energy to reach their 300-1,200 km altitudes. Regardless of destination, rockets must accelerate to approximately 28,000 km/h (17,500 mph) to achieve orbit.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Launch economics significantly influence satellite deployment strategies. Current costs range from approximately $2,700 per kilogram to LEO on SpaceX's partially reusable Falcon 9 to around $20,000 per kilogram on smaller vehicles like Rocket Lab's Electron. These figures represent a dramatic reduction from historical costs that often exceeded $50,000 per kilogram before reusable rocket technology.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Once the rocket reaches space, the fairing separates to expose the satellite, and precisely calculated engine burns position the spacecraft in its target orbit. After deployment, the satellite unfolds solar arrays and communication antennas, then uses onboard thrusters for final orbital adjustments. This intricate choreography of engineering and physics transforms years of planning into operational reality.",
                                    style={**_paragraph__style}
                                )
                            ], md=7)
                        ]),

                        html.Hr(className="my-4"),

                        html.H5("Launch Systems", className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    fact_data["launches"]["btn-1"]["button_title"],
                                    id="sat-launches-btn-1",
                                    color="warning",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["launches"]["btn-2"]["button_title"],
                                    id="sat-launches-btn-2",
                                    color="warning",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["launches"]["btn-3"]["button_title"],
                                    id="sat-launches-btn-3",
                                    color="warning",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2"),
                            dbc.Col([
                                dbc.Button(
                                    fact_data["launches"]["btn-4"]["button_title"],
                                    id="sat-launches-btn-4",
                                    color="warning",
                                    outline=True,
                                    className="w-100 mb-2",
                                    style={**_fact_button_collapsed__style}
                                )
                            ], md=6, lg=3, className="mb-2")
                        ]),

                        dbc.Modal([
                            dbc.ModalHeader(dbc.ModalTitle(id="launches-modal-title")),
                            dbc.ModalBody(id="launches-modal-body"),
                            dbc.ModalFooter(
                                dbc.Button("Close", id="close-launches-modal", className="ms-auto")
                            )
                        ], id="launches-modal", size="lg", is_open=False)
                    ])
                ], className="mb-4 shadow-sm")
            ]),

            # Ownership Section
            html.Section(id="owners", children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("Satellite Ownership", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Img(src="/assets/images/copernicus_programme.jpg",
                                         style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                                html.P(
                                    "Satellites are owned by governments, companies, and international organizations.",
                                    className="text-muted small mt-2",
                                    style={'textAlign': 'center', 'width': '100%'})
                            ], style={'textAlign': 'center'}),

                            dbc.Col([
                                html.P(
                                    "Satellites are owned by a diverse range of entities, reflecting the global "
                                    "nature of space activity. Government agencies, such as NASA in the United States "
                                    "and the European Space Agency (ESA), lead in satellite launches for national security, "
                                    "scientific research, and environmental monitoring. Their satellites support vital"
                                    " projects,  like climate studies and space exploration, ensuring national and "
                                    "international interests are met.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Private companies have rapidly emerged as key players in satellite ownership. "
                                    "SpaceX, for example, operates a growing constellation of communication satellites as "
                                    "part of its Starlink program, aimed at providing global internet coverage. OneWeb and "
                                    "other private firms contribute similarly, using satellites to support industries "
                                    "ranging from telecommunications to Earth observation.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "Additionally, international collaborations, such as the European Union's Copernicus "
                                    "program, highlight efforts to manage and share satellite data globally. These "
                                    "partnerships benefit all by supporting projects related to disaster management, "
                                    "agriculture, and environmental conservation.",
                                    style={**_paragraph__style}
                                ),
                                html.P(
                                    "The ownership of satellites underscores a dynamic mix of public and private entities, "
                                    "each contributing to the rapidly expanding capabilities of satellite technology "
                                    "and its impact on modern life.",
                                    style={**_paragraph__style}
                                )
                            ], md=7)
                        ]),

                        html.Hr(className="my-4"),

                        html.P("Distribution by ownership type (example data):", className="mb-2 small text-muted"),
                        dbc.Progress([
                            dbc.Progress(value=35, color="primary", bar=True, children="Commercial 35%"),
                            dbc.Progress(value=30, color="info", bar=True, children="Government 30%"),
                            dbc.Progress(value=20, color="success", bar=True, children="Military 20%"),
                            dbc.Progress(value=15, color="warning", bar=True, children="Academic 15%")
                        ], className="mb-4", style={"height": "30px"})
                    ])
                ], className="mb-4 shadow-sm")
            ])
        ], style={'maxWidth': '1200px', 'margin': '0 auto'})
    ])

    return layout
# layout_home.py - Updated for Callback Integration
import sys
from dash import html, get_asset_url, dcc

## Internal Scripts
sys.path.append("../../")

# Get styles
from app.styles.styles_sat_explained import (_main_page__style, _navbar_tabs__style,
                                             _navbar__style, _tab_content__style, _tab_header__style,
                                             _section_title__style, _image__style, _image_caption__style,
                                             _image_box_alignment__style, _image_box__style,
                                             _paragraph__style, _text__style, _text_section_child__style,
                                             _text_section_parent__style, _fact_button_collapsed__style,
                                             _fact_section__style)

# Get button details
from app.content.content_buttons import (fact_data)

"""
App Layout
"""

def create_dash_layout(app):
    layout = html.Div(style={**_main_page__style}, children=[

        # Navigation Bar - Left Side with improved styling
        html.Div([
            html.A("History", href="#history", className="nav-link",
                   style={**_navbar_tabs__style}),
            html.A("Applications", href="#applications", className="nav-link",
                   style={**_navbar_tabs__style}),
            html.A("Getting to Orbit", href="#launches", className="nav-link",
                   style={**_navbar_tabs__style}),
            html.A("Ownership", href="#owners", className="nav-link",
                   style={**_navbar_tabs__style})
        ], style={**_navbar__style}),

        # Main content with improved spacing
        html.Div(style={**_tab_content__style}, children=[

            # Page title with improved styling
            html.H1("Satellites Explained", style={**_tab_header__style}),

            ## -- History of Satellites -- ##
            html.Section(id="history", children=[
                html.Div([
                    # Flexbox container for the columns
                    html.Div([
                        # Title and Image (aligned to the left side)
                        html.Div([
                            # Title with improved styling
                            html.H3("A Brief History of Satellites", style={**_section_title__style}),

                            # Image with enhanced styling
                            html.Div([
                                html.Img(src="/assets/images/sputnik.jpg", alt="Sputnik Satellite",
                                         style={**_image__style}),

                                # Image caption with improved styling
                                html.P(
                                    "Sputnik 1 - The first artificial satellite, "
                                    "launched by the Soviet Union in 1957. (Credit: Don Mitchell)",
                                    style={**_image_caption__style})
                            ], style={**_image_box_alignment__style})
                        ], style={**_image_box__style}),

                        # Text content with improved typography
                        html.Div([
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
                            ),
                        ], style={**_text__style}),
                    ], style={**_text_section_child__style})
                ], style={**_text_section_parent__style})
            ]),

            # Fact buttons with improved styling - actual content managed by callbacks
            html.Div([
                html.Button(fact_data['history']['btn-1']['button_title'], id='sat-history-btn-1', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['history']['btn-2']['button_title'], id='sat-history-btn-2', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['history']['btn-3']['button_title'], id='sat-history-btn-3', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['history']['btn-4']['button_title'], id='sat-history-btn-4', style={**_fact_button_collapsed__style}),
            ], style={**_fact_section__style}),

            ## -- Satellite Applications -- ##
            html.Section(id="applications", children=[
                html.Div([
                    # Flexbox container for the columns
                    html.Div([
                        # Title and Image (aligned to the left side)
                        html.Div([
                            # Title
                            html.H3("Satellite Applications", style={**_section_title__style}),

                            # Image below the title
                            html.Div([
                                html.Img(src="/assets/images/jwst.jpg", alt="James Webb Space Telescope",
                                         style={**_image__style}),

                                # Image caption
                                html.P(
                                    "James Webb Space Telescope - launched in 2023 to explore the universe "
                                    "and study the formation of stars and galaxies. (Credit: NASA/Chris Gunn)",
                                    style={**_image_caption__style})
                            ], style={**_image_box_alignment__style})
                        ], style={**_image_box__style}),

                        # Column 1 - text with improved paragraph styling
                        html.Div([
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
                            ),
                        ], style={**_text__style}),
                    ], style={**_text_section_child__style})
                ], style={**_text_section_parent__style})
            ]),

            # Fact buttons for satellite applications
            html.Div([
                html.Button(fact_data['purpose']['btn-1']['button_title'], id='sat-purpose-btn-1', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['purpose']['btn-2']['button_title'], id='sat-purpose-btn-2', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['purpose']['btn-3']['button_title'], id='sat-purpose-btn-3', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['purpose']['btn-4']['button_title'], id='sat-purpose-btn-4', style={**_fact_button_collapsed__style}),
            ], style={**_fact_section__style}),

            ## -- Getting into Orbit -- ##
            html.Section(id="launches", children=[
                html.Div([
                    # Flexbox container with improved layout
                    html.Div([
                        # Title and Image (aligned to the left side)
                        html.Div([
                            # Title with consistent styling
                            html.H3("Getting into Orbit", style={**_section_title__style}),

                            # Image container with enhanced styling
                            html.Div([
                                html.Img(src="/assets/images/iridium_fairing.jpg", alt="Iridium Satellite Fairing",
                                         style={**_image__style}),

                                # Image caption with consistent styling
                                html.P(
                                    "Iridium satellite being enclosed inside the payload fairing of SpaceX's "
                                    "Falcon 9 rocket. (Credit: Iridium)",
                                    style={**_image_caption__style})
                            ], style={**_image_box_alignment__style})
                        ], style={**_image_box__style}),

                        # Text content with improved style
                        html.Div([
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
                            ),
                        ], style={**_text__style}),
                    ], style={**_text_section_child__style})
                ], style={**_text_section_parent__style})
            ]),

            # Fact buttons for launch section - content managed by callbacks
            html.Div([
                html.Button(fact_data['launches']['btn-1']['button_title'], id='sat-launches-btn-1', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['launches']['btn-2']['button_title'], id='sat-launches-btn-2', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['launches']['btn-3']['button_title'], id='sat-launches-btn-3', style={**_fact_button_collapsed__style}),
                html.Button(fact_data['launches']['btn-4']['button_title'], id='sat-launches-btn-4', style={**_fact_button_collapsed__style}),
            ], style={**_fact_section__style}),

            ## -- Who owns Satellites? -- ##
            html.Section(id="owners", children=[
                html.Div([
                    # Flexbox container for the columns
                    html.Div([
                        # Title and Image (aligned to the left side)
                        html.Div([
                            # Title with improved styling
                            html.H3("Who Owns Satellites?", style={**_section_title__style}),

                            # Image with enhanced styling
                            html.Div([
                                html.Img(src="/assets/images/copernicus_programme.jpg",
                                         alt="Copernicus Programme Contributors",
                                         style={**_image__style}),

                                # Image caption with improved styling
                                html.P(
                                    "Contributors to Copernicus, the European Union's Earth Observation Programme."
                                    " (www.copernicus.eu)",
                                    style={**_image_caption__style})
                            ], style={**_image_box_alignment__style})
                        ], style={**_image_box__style}),

                        # Text content with improved typography
                        html.Div([
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
                        ], style={**_text__style}),
                    ], style={**_text_section_child__style})
                ], style={**_text_section_parent__style})
            ]),

            # Hidden div for button initialization callback
            html.Div(id='dummy-trigger', children='trigger', style={'display': 'none'})

        ])  # End of RHS section
    ])  # End of layout object

    return layout
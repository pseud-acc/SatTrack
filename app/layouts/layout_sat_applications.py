# layout_sat_applications.py
import sys
from dash import html
import dash_bootstrap_components as dbc

sys.path.append("../../")

from app.styles.styles_sat_explained import _main_page__style, _section_title__style

# Import components
from app.layouts.components.sat_applications.navigation_cards import create_navigation_cards
from app.layouts.components.sat_applications.stats_dashboard import create_stats_dashboard
from app.layouts.components.sat_applications.sections.history_section import create_history_section
from app.layouts.components.sat_applications.sections.applications_section import create_applications_section
from app.layouts.components.sat_applications.sections.launches_section import create_launches_section
from app.layouts.components.sat_applications.sections.ownership_section import create_ownership_section


def create_dash_layout(app):
    """
    Create the main Dash layout for satellite applications educational page.

    Args:
        app: Dash application instance

    Returns:
        layout: Complete Dash layout
    """
    layout = html.Div(style={**_main_page__style}, children=[

        # Header
        html.Div([
            html.H1("Satellites Explained",
                    style={**_section_title__style, 'textAlign': 'center', 'fontSize': '2.5em'}),
            html.P("Discover the history, applications, and technology behind Earth's orbital infrastructure",
                   style={'textAlign': 'center', 'color': '#a0a0a0', 'fontSize': '1.1em', 'marginBottom': '40px'})
        ]),

        # Section Navigation Cards
        create_navigation_cards(),

        # Statistics Dashboard
        create_stats_dashboard(),

        # Main Content Sections
        html.Div([
            # History Section
            create_history_section(),

            # Applications Section
            create_applications_section(),

            # Launch Systems Section
            create_launches_section(),

            # Ownership Section
            create_ownership_section()

        ], style={'maxWidth': '1200px', 'margin': '0 auto'})
    ])

    return layout

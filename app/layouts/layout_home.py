# layout_home.py
from dash import html, dcc
import dash_bootstrap_components as dbc


def _feature(title, text):
    """One feature card (assets/06_home.css: .st-home-card)."""
    return dbc.Col(html.Div([html.H3(title, className="st-home-card-title"), html.P(text, className="st-home-card-text")],
                            className="st-home-card"), md=6, lg=3)


def _stat(value, label):
    return html.Div([html.Div(value, className="st-home-stat-value"), html.Div(label, className="st-home-stat-label")],
                    className="st-home-stat")


def create_dash_layout(app):
    """The home page (3.12 step 5): the same words as before, laid out on the design tokens (assets/06_home.css)."""
    layout = html.Div([
        # Hero
        html.Section([
            html.H1("Track Satellites in Real-Time", className="st-home-title"),
            html.P("Watch thousands of satellites orbit Earth. Explore their missions, "
                   "trajectories, and real-time positions in 3D.", className="st-home-lede"),
            dbc.Button("Launch Tracker", id="get-started-button", color="primary", size="lg",
                       href="/sat_visualisation", className="st-home-cta"),
            html.Div([
                _stat("15,000+", "Satellites"),
                _stat("Live", "Real-Time Tracking"),
                _stat("Free", "Open Source Codebase"),
            ], className="st-home-stats"),
        ], className="st-home-hero"),

        # Features
        html.Section([
            html.H2("Explore Satellite Data", className="st-home-h2"),
            dbc.Row([
                _feature("3D Visualization", "Interactive globe showing satellite positions and orbital paths in real-time."),
                _feature("Advanced Filters", "Search by satellite name, orbit type, owner, purpose, and launch year."),
                _feature("Ground Tracks", "See 2D ground paths and predict when satellites pass overhead."),
                _feature("Data Export", "Download satellite data tables for analysis and research projects."),
            ], className="g-3"),
        ], className="st-home-section"),

        # Data sources
        html.Section([
            html.H2("Data Sources", className="st-home-h2"),
            html.P("Powered by accurate, up-to-date information:"),
            html.Ul(_data_source_items() + [
                html.Li("SGP4 propagator for precise calculations"),
                html.Li("Updated daily for accuracy")
            ], className="st-home-sources"),
        ], className="st-home-section"),
    ], className="st-home")

    return layout

def _data_source_items():
    """Data-source list for the data shown (the pipeline's Space-Track + GCAT files)."""
    return [
        html.Li(["Orbital data (GP/TLE elements, SATCAT): USSPACECOM via ",
                 dcc.Link("Space-Track.org", href="https://www.space-track.org/", className="st-home-link")]),
        html.Li(["Launch, owner and mission details: ",
                 dcc.Link("GCAT (J. McDowell)", href="https://planet4589.org/space/gcat/",
                          className="st-home-link")]),
        html.Li("Public TLEs must not be used for conjunction (collision) assessment "
                "(Space-Track User Agreement)."),
    ]

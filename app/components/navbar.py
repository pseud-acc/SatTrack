# navbar.py
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# Define the navigation bar for the app
navbar = dbc.Navbar(
    [
        dbc.Container(
            [
                # Brand/Logo
                dbc.NavbarBrand("SatTrack", href="/", className="ms-2 fs-4 fw-bold"),

                # Toggler for mobile
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),

                # Collapsible nav links
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Home", href="/", id="nav-home")),
                            dbc.NavItem(dbc.NavLink("Live Tracker", href="/sat_visualisation", id="nav-viz")),
                            dbc.NavItem(dbc.NavLink("Learn", href="/sat_applications", id="nav-learn"))
                        ],
                        className="ms-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    is_open=False,
                    navbar=True,
                ),
            ],
            fluid=True,
        )
    ],
    color="dark",
    dark=True,
    className="mb-3",
    sticky="top",
)

# Callback to highlight the active page in the navigation bar
def update_navbar(app):
    @app.callback(
        [Output(f"page-{page}", "active") for page in ["home", "sat_visualisation"]],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        if pathname == "/":
            return True, False
        return [pathname == f"/{page}" for page in ["home", "sat_visualisation", "sat_applications"]]
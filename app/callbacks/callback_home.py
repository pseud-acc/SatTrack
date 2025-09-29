# app/callbacks/callback_home.py
## Packages

import sys
from dash.dependencies import Input, Output

## Internal Scripts

# paths
sys.path.append("../../")

def get_callbacks(app):
    @app.callback(
        Output("url", "pathname"),
        Input("get-started-button", "n_clicks"),
    )
    def navigate_to_visualization_page(n_clicks):
        if n_clicks:
            return "/sat_visualisation"
        return "/"
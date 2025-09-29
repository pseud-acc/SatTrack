# callback_sat_applications.py
import sys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html, dcc, callback_context

sys.path.append("../../")

from app.styles.styles_sat_explained import _fact_button_expanded_text__style
from app.content.content_buttons import fact_data


def get_callbacks(app):
    # History section modal callbacks
    @app.callback(
        [Output("history-modal", "is_open"),
         Output("history-modal-title", "children"),
         Output("history-modal-body", "children")],
        [Input("sat-history-btn-1", "n_clicks"),
         Input("sat-history-btn-2", "n_clicks"),
         Input("sat-history-btn-3", "n_clicks"),
         Input("sat-history-btn-4", "n_clicks"),
         Input("close-history-modal", "n_clicks")],
        [State("history-modal", "is_open")]
    )
    def toggle_history_modal(btn1, btn2, btn3, btn4, close, is_open):
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "close-history-modal":
            return False, "", ""

        if button_id.startswith("sat-history-btn"):
            btn_num = button_id.split("-")[-1]
            btn_key = f"btn-{btn_num}"
            data = fact_data["history"][btn_key]

            title = data["sat_name"]
            body = html.Div([
                html.P([html.Strong("Launch Date: "), data["launch_date"]], className="mb-2"),
                html.Hr(),
                html.Ul([
                    html.Li(data["fact_1"]),
                    html.Li(data["fact_2"]),
                    html.Li(data["fact_3"])
                ], className="mb-3"),
                html.A("Learn more on NASA", href=data["nasa_link"],
                       target="_blank", className="btn btn-outline-info btn-sm")
            ])

            return True, title, body

        raise PreventUpdate

    # Purpose section modal callbacks
    @app.callback(
        [Output("purpose-modal", "is_open"),
         Output("purpose-modal-title", "children"),
         Output("purpose-modal-body", "children")],
        [Input("sat-purpose-btn-1", "n_clicks"),
         Input("sat-purpose-btn-2", "n_clicks"),
         Input("sat-purpose-btn-3", "n_clicks"),
         Input("sat-purpose-btn-4", "n_clicks"),
         Input("close-purpose-modal", "n_clicks")],
        [State("purpose-modal", "is_open")]
    )
    def toggle_purpose_modal(btn1, btn2, btn3, btn4, close, is_open):
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "close-purpose-modal":
            return False, "", ""

        if button_id.startswith("sat-purpose-btn"):
            btn_num = button_id.split("-")[-1]
            btn_key = f"btn-{btn_num}"
            data = fact_data["purpose"][btn_key]

            title = data["sat_name"]
            body = html.Div([
                html.P([html.Strong("Launch Date: "), data["launch_date"]], className="mb-2"),
                html.Hr(),
                html.Ul([
                    html.Li(data["fact_1"]),
                    html.Li(data["fact_2"]),
                    html.Li(data["fact_3"])
                ], className="mb-3"),
                html.A("Learn more on NASA", href=data["nasa_link"],
                       target="_blank", className="btn btn-outline-success btn-sm")
            ])

            return True, title, body

        raise PreventUpdate

    # Launches section modal callbacks
    @app.callback(
        [Output("launches-modal", "is_open"),
         Output("launches-modal-title", "children"),
         Output("launches-modal-body", "children")],
        [Input("sat-launches-btn-1", "n_clicks"),
         Input("sat-launches-btn-2", "n_clicks"),
         Input("sat-launches-btn-3", "n_clicks"),
         Input("sat-launches-btn-4", "n_clicks"),
         Input("close-launches-modal", "n_clicks")],
        [State("launches-modal", "is_open")]
    )
    def toggle_launches_modal(btn1, btn2, btn3, btn4, close, is_open):
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "close-launches-modal":
            return False, "", ""

        if button_id.startswith("sat-launches-btn"):
            btn_num = button_id.split("-")[-1]
            btn_key = f"btn-{btn_num}"
            data = fact_data["launches"][btn_key]

            title = data["sat_name"]
            body = html.Div([
                html.P([html.Strong("First Launch: "), data["launch_date"]], className="mb-2"),
                html.Hr(),
                html.Ul([
                    html.Li(data["fact_1"]),
                    html.Li(data["fact_2"]),
                    html.Li(data["fact_3"])
                ], className="mb-3"),
                html.A("Learn more on NASA", href=data["nasa_link"],
                       target="_blank", className="btn btn-outline-warning btn-sm")
            ])

            return True, title, body

        raise PreventUpdate
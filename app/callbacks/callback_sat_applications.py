#!/usr/bin/env python

"""
Callbacks for satellite applications educational page.

This module handles interactive modal dialogs for different satellite information sections:
- History section modals
- Applications/Purpose section modals
- Launch systems section modals

Functions:
    register: Main callback registration function
    _create_modal_body: Helper to generate modal content
    _create_modal_callback: Generic callback factory for modal toggles

Todo:
    *
"""

## Packages
import sys
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html, callback_context

sys.path.append("../../")

from app.content.content_buttons import fact_data


# ===========================
# Helper Functions
# ===========================

def _create_modal_body(data, button_color="info"):
    """
    Create standardized modal body content from fact data.

    Args:
        data (dict): Dictionary containing satellite facts with keys:
            - sat_name: Satellite name
            - launch_date: Launch date string
            - fact_1, fact_2, fact_3: Facts to display
            - nasa_link: External link URL
        button_color (str): Bootstrap color class for the external link button

    Returns:
        html.Div: Formatted modal body content
    """
    return html.Div([
        html.P([html.Strong("Launch Date: "), data["launch_date"]], className="mb-2"),
        html.Hr(),
        html.Ul([
            html.Li(data["fact_1"]),
            html.Li(data["fact_2"]),
            html.Li(data["fact_3"])
        ], className="mb-3"),
        html.A(
            "Learn more on NASA",
            href=data["nasa_link"],
            target="_blank",
            className=f"btn btn-outline-{button_color} btn-sm"
        )
    ])


def _handle_modal_button_click(ctx, section_name, close_button_id, button_prefix, button_color="info"):
    """
    Generic handler for modal button clicks.

    Args:
        ctx: Dash callback_context
        section_name (str): Name of the section in fact_data (e.g., "history", "purpose", "launches")
        close_button_id (str): ID of the close button
        button_prefix (str): Prefix of the button IDs (e.g., "sat-history-btn")
        button_color (str): Bootstrap color for the modal link button

    Returns:
        tuple: (is_open, title, body) for the modal

    Raises:
        PreventUpdate: If no trigger or unknown button
    """
    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Handle close button
    if button_id == close_button_id:
        return False, "", ""

    # Handle section buttons
    if button_id.startswith(button_prefix):
        btn_num = button_id.split("-")[-1]
        btn_key = f"btn-{btn_num}"
        data = fact_data[section_name][btn_key]

        title = data["sat_name"]
        body = _create_modal_body(data, button_color)

        return True, title, body

    raise PreventUpdate


# ===========================
# Callback Registration
# ===========================

def register(app):
    """
    Register all callbacks for satellite applications page.

    This function registers modal toggle callbacks for three sections:
    - History section (4 buttons)
    - Applications/Purpose section (4 buttons)
    - Launch systems section (4 buttons)

    Args:
        app: Dash application instance

    Returns:
        None
    """

    # -------------------------
    # History Section Modal
    # -------------------------
    @app.callback(
        [
            Output("history-modal", "is_open"),
            Output("history-modal-title", "children"),
            Output("history-modal-body", "children")
        ],
        [
            Input("sat-history-btn-1", "n_clicks"),
            Input("sat-history-btn-2", "n_clicks"),
            Input("sat-history-btn-3", "n_clicks"),
            Input("sat-history-btn-4", "n_clicks"),
            Input("close-history-modal", "n_clicks")
        ],
        [State("history-modal", "is_open")]
    )
    def toggle_history_modal(btn1, btn2, btn3, btn4, close, is_open):
        """
        Toggle history section modal and populate content.

        Args:
            btn1-4 (int): Click counts for each history button
            close (int): Click count for close button
            is_open (bool): Current modal state

        Returns:
            tuple: (is_open, title, body) for the modal
        """
        return _handle_modal_button_click(
            callback_context,
            section_name="history",
            close_button_id="close-history-modal",
            button_prefix="sat-history-btn",
            button_color="info"
        )

    # -------------------------
    # Applications/Purpose Section Modal
    # -------------------------
    @app.callback(
        [
            Output("purpose-modal", "is_open"),
            Output("purpose-modal-title", "children"),
            Output("purpose-modal-body", "children")
        ],
        [
            Input("sat-purpose-btn-1", "n_clicks"),
            Input("sat-purpose-btn-2", "n_clicks"),
            Input("sat-purpose-btn-3", "n_clicks"),
            Input("sat-purpose-btn-4", "n_clicks"),
            Input("close-purpose-modal", "n_clicks")
        ],
        [State("purpose-modal", "is_open")]
    )
    def toggle_purpose_modal(btn1, btn2, btn3, btn4, close, is_open):
        """
        Toggle applications/purpose section modal and populate content.

        Args:
            btn1-4 (int): Click counts for each purpose button
            close (int): Click count for close button
            is_open (bool): Current modal state

        Returns:
            tuple: (is_open, title, body) for the modal
        """
        return _handle_modal_button_click(
            callback_context,
            section_name="purpose",
            close_button_id="close-purpose-modal",
            button_prefix="sat-purpose-btn",
            button_color="success"
        )

    # -------------------------
    # Launch Systems Section Modal
    # -------------------------
    @app.callback(
        [
            Output("launches-modal", "is_open"),
            Output("launches-modal-title", "children"),
            Output("launches-modal-body", "children")
        ],
        [
            Input("sat-launches-btn-1", "n_clicks"),
            Input("sat-launches-btn-2", "n_clicks"),
            Input("sat-launches-btn-3", "n_clicks"),
            Input("sat-launches-btn-4", "n_clicks"),
            Input("close-launches-modal", "n_clicks")
        ],
        [State("launches-modal", "is_open")]
    )
    def toggle_launches_modal(btn1, btn2, btn3, btn4, close, is_open):
        """
        Toggle launch systems section modal and populate content.

        Args:
            btn1-4 (int): Click counts for each launches button
            close (int): Click count for close button
            is_open (bool): Current modal state

        Returns:
            tuple: (is_open, title, body) for the modal
        """
        return _handle_modal_button_click(
            callback_context,
            section_name="launches",
            close_button_id="close-launches-modal",
            button_prefix="sat-launches-btn",
            button_color="warning"
        )

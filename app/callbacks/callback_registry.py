#!/usr/bin/env python

"""
Central callback registration - imports and registers all callbacks.
Only this file is imported by run_app_dev_v2.py

Functions:
    register_all_callbacks: Main entry point for registering all app callbacks

Todo:
    *
"""

from app.callbacks import (
    callback_3d_viz,
    callback_2d_viz,
    callback_table,
    callback_filters,
    callback_navbar,
    callback_sat_applications
)


def register_all_callbacks(app):
    """
    Register all application callbacks.

    @param app: (Dash app object) Dash app instance

    @return: None
    """
    callback_3d_viz.register(app)
    callback_2d_viz.register(app)
    callback_table.register(app)
    callback_filters.register(app)
    callback_navbar.register(app)
    callback_sat_applications.register(app)

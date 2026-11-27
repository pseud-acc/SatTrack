#!/usr/bin/env python

"""
Central callback registration - imports and registers all callbacks.
Only this file is imported by run_app.py + run_app_dev.py to keep those files clean.

Functions:
    register_all_callbacks: Main entry point for registering all app callbacks

Todo:
    *
"""

from app.callbacks import (
    callback_2d_viz,
    callback_tabs,
    callback_table,
    callback_filters,
    callback_navbar,
    callback_viewer,
)
from app.core.viewer import viewer_enabled


def register_all_callbacks(app):
    """
    Register all application callbacks.

    @param app: (Dash app object) Dash app instance

    @return: None
    """
    callback_2d_viz.register(app)
    callback_tabs.register(app)
    callback_table.register(app)
    callback_filters.register(app)
    callback_navbar.register(app)
    if viewer_enabled():   # the Cesium viewer flag (app/core/viewer.py); off by default
        callback_viewer.register(app)

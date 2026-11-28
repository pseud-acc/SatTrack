#!/usr/bin/env python

"""

This module defines dash app callbacks used in the SatTrack visualisation.

Example:

        $ python callback_sat_visualisations.py

Functions:
    get_callbacks: wrapper function for callbacks
    update_3dviz: callback function for interactive 3d satellite visualisation
    update_2dviz: callback function for interactive 2d satellite visualisation
    update_tbl: callback function for table of satellites
    update_filter_spec: the panel's controls -> the filter-spec store
    update_panel_summary: the live count, type counts, hints, chips and row summaries
    panel_controls: Space junk mode, chip removal and Clear all

Todo:
    * 

"""

## Packages

import sys
import numpy as np
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash import Dash, callback_context, ctx, no_update


## Internal Modules

# paths
sys.path.append("../../")

# app data
from app.core.state import get_app_data
# app functions
from app.helper.helper__app_data import sidebar_filter_spec, OBJECT_TYPES, JUNK_TYPES
from app.core import filter_spec as spec_rules
from app.helper.helper__filter_display import (CONTROLS, CHIPS, REMOVABLE_CHIPS, ROWS, default_controls,
                                               widened_controls, panel_summary)
from app.layouts.components.filters.type_filter import type_options, type_hints
from app.layouts.components.filters.match_count import count_children
from app.core.viewer import viewer_state


# Callback wrapper function
def register(app):
    ''' 
    Wrapper function that defines callbacks using app instantiation.

    @param app: (dash app object) instantiated app object

    '''

    # Get app data
    app_data = get_app_data()
    filter_table = app_data['filter']['table']
    globe = viewer_state()["enabled"]   # without the globe the count is of payloads (#83)

    # >>> Define Callbacks <<<

    # The panel's controls as callback inputs, in sidebar_filter_spec's argument order (helper__filter_display.CONTROLS)
    control_inputs = [Input(cid, 'value') for cid in CONTROLS.values()]

    # The search lists (name and SATCAT number) are set once in the layout and never rebuilt (roadmap 3.3b, Q8 S2):
    # rebuilding them re-indexed ~16k options on every filter change. A picked satellite outside the other filters
    # shows as a chip, and the count says it matches 0.

    '''------------------------
    The filter spec (roadmap 3.3a)
    -------------------------
    Interactive Inputs: every panel control
    Outputs: the page's filter-spec store, which the globe, the 2D map and the list read (Q7). The page renders
    the starting spec into the store, so nothing runs at load.
    '''

    @app.callback(Output('filter-spec', 'data'), control_inputs, prevent_initial_call=True)
    def update_filter_spec(*values):
        c = dict(zip(CONTROLS, values))
        for name in ("owner", "launchvehicle", "purpose", "types", "constellation", "system"):
            c[name] = c[name] or []
        spec = sidebar_filter_spec(**c)
        return None if spec is None else spec_rules.validate(spec)

    '''------------------------
    What the panel shows about its values (roadmap 3.3b, D-044)
    -------------------------
    Interactive Inputs: every panel control
    Outputs: the live count, the type switches' "matching / total", the zero-match hints, the chips, "Clear all" and
    the "More filters" rows' summaries. Worked out on the server from the same values as the spec (Q4); the page
    renders the starting summary, so nothing runs at load.
    '''

    @app.callback(
        [Output('filter-count', 'children'),
         Output('type-filter-checkbox', 'options'),
         Output('type-hint', 'children'),
         Output('filter-clear-all', 'hidden')]
        + [Output(f'chip-{name}', 'hidden') for name in CHIPS]
        + [Output(f'chip-{name}-text', 'children') for name in CHIPS]
        + [Output(f'more-{name}-summary', 'children') for name in ROWS],
        control_inputs,
        prevent_initial_call=True
    )
    def update_panel_summary(*values):
        summary = panel_summary(filter_table, dict(zip(CONTROLS, values)))
        chips = summary["chips"]
        return ([count_children(summary, globe), type_options(summary), type_hints(summary), not summary["changed"]]
                + [chips[name] is None for name in CHIPS]
                + [chips[name] or "" for name in CHIPS]
                + [summary["rows"][name] for name in ROWS])

    '''------------------------
    Space junk mode, chip removal and Clear all (roadmap 3.3a, 3.3b; owner, 26 Nov 2026)
    -------------------------
    Interactive Inputs: the junk switch, the type switches, each chip's remove button, Clear all
    Outputs: the switch, the types, the status, the status to restore, and every other control
    Rocket bodies and debris are always Inactive (D-053), so junk mode on also sets status to All (remembering the status
    before); off restores it. Ticking both junk types by hand turns the switch on, unticking either turns it off;
    neither touches the status. A chip's remove button widens its control; Clear all restores the opening values
    (D-049). One callback owns these outputs, so no control is set by two callbacks.
    '''

    others = [k for k in CONTROLS if k not in ("status", "types")]

    @app.callback(
        [Output('junk-mode-switch', 'value'),
         Output('type-filter-checkbox', 'value'),
         Output('status-filter-checkbox', 'value'),
         Output('status-before-junk', 'data')]
        + [Output(CONTROLS[k], 'value') for k in others],
        [Input('junk-mode-switch', 'value'),
         Input('type-filter-checkbox', 'value'),
         Input('filter-clear-all', 'n_clicks')]
        + [Input(f'chip-x-{name}', 'n_clicks') for name in REMOVABLE_CHIPS],
        [State('status-filter-checkbox', 'value'),
         State('status-before-junk', 'data')],
        prevent_initial_call=True
    )
    def panel_controls(junk, types, *rest):
        status, status_before = rest[-2], rest[-1]
        keep = [no_update] * len(others)
        trigger = ctx.triggered_id
        types = list(types or [])
        if trigger == 'filter-clear-all':
            d = default_controls()
            return [False, d["types"], d["status"], None] + [d[k] for k in others]
        if isinstance(trigger, str) and trigger.startswith('chip-x-'):
            name = trigger[len('chip-x-'):]
            wide = widened_controls()[name]
            if name == "status":
                return [no_update, no_update, wide, no_update] + keep
            return [no_update] * 4 + [wide if k == name else no_update for k in others]
        if trigger == 'junk-mode-switch':
            if junk:
                types = [t for t in OBJECT_TYPES if t in types or t in JUNK_TYPES]
                return [no_update, types, "All", status] + keep
            types = [t for t in types if t not in JUNK_TYPES]
            return [no_update, types, status_before if status_before is not None else status, None] + keep
        both = all(t in types for t in JUNK_TYPES)
        if bool(junk) == both:
            raise PreventUpdate
        return [both, no_update, no_update, no_update if both else None] + keep

    '''------------------------
    Mobile responsiveness
    -------------------------
    Interactive Inputs: Toggle filter button
    Outputs: Filter collapse state and icon rotation
    Runs in the browser (D-052; owner, 27 Nov 2026: opening Filters on a phone waited for a server round trip).
    '''

    # The search list (assets/07_search.js) shows the picked satellite; when a chip's x or Clear all changes it,
    # tell the list. Runs in the browser; returns no_update (the title output is only a required target).
    app.clientside_callback(
        """function (value) {
            if (window.sattrackSearch) window.sattrackSearch.setSelected(value);
            return window.dash_clientside.no_update;
        }""",
        Output("sat-search", "title"),
        Input("satcatid-filter-dropdown", "value"),
    )

    app.clientside_callback(
        """function (n, isOpen) {
            const open = n ? !isOpen : isOpen;
            return [open, open ? "st-icon st-icon-chevron-up" : "st-icon st-icon-chevron-down"];
        }""",
        Output("filter-collapse", "is_open"),
        Output("toggle-icon", "className"),
        Input("toggle-filters", "n_clicks"),
        State("filter-collapse", "is_open"),
    )

    '''------------------------
    Desktop panel strip (3.12 step 3)
    -------------------------
    Interactive Inputs: the panel's fold button
    Outputs: the tracker row's class (st-panel-folded narrows the panel to a strip; assets/04_shell.css) and the icon
    '''

    @app.callback(
        [
            Output("tracker-row", "className"),
            Output("panel-strip-icon", "className")
        ],
        [Input("panel-strip-toggle", "n_clicks")],
        [State("tracker-row", "className")],
        prevent_initial_call=True
    )
    def toggle_panel_strip(n, row_class):
        classes = (row_class or "").split()
        folded = "st-panel-folded" not in classes
        classes = [c for c in classes if c != "st-panel-folded"] + (["st-panel-folded"] if folded else [])
        icon = "st-icon st-icon-chevron-right" if folded else "st-icon st-icon-chevron-left"
        return " ".join(classes), icon

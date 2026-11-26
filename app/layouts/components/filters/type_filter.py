"""
Object type filter (roadmap 3.3a; D-016): payloads, rocket bodies and debris as switches in the panel, plus "Space junk
mode" for both junk types. They go into the filter spec as an `object_type in [...]` clause (Q5), which drives the
globe and the other views. UNKNOWN is never offered, so it stays hidden (D-011).

Almost every rocket body and debris object is Inactive in the data (all but 6 of 12,398 on 21 Nov 2026), so the note
under the switches says so; Space junk mode also ticks Inactive (owner, 26 Nov 2026; app/callbacks/callback_filters.py).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import OBJECT_TYPES, DEFAULT_TYPES

LABELS = {"PAYLOAD": "Payloads", "ROCKET BODY": "Rocket bodies", "DEBRIS": "Debris"}
SWATCH = {"PAYLOAD": "st-swatch-payload", "ROCKET BODY": "st-swatch-rocket", "DEBRIS": "st-swatch-debris"}


def _option(object_type, total):
    return {
        "label": html.Span([
            html.Span(className=f"st-swatch {SWATCH[object_type]}"),
            html.Span(LABELS[object_type], className="st-type-name"),
            html.Span(f"{total:,}", className="st-type-total", id=f"type-total-{object_type.replace(' ', '-').lower()}"),
        ], className="st-type-option"),
        "value": object_type,
    }


def create_type_filter(type_totals):
    """
    @param type_totals: (dict) object type -> number of objects of that type in the objects dataset
    @return: html.Div with the type checklist (id type-filter-checkbox), the junk switch (junk-mode-switch), the note,
             and the store that remembers the status from before junk mode (status-before-junk)
    """
    return html.Div([
        html.Label("Object Type", className="st-lbl"),
        dcc.Checklist(
            options=[_option(t, int(type_totals.get(t, 0))) for t in OBJECT_TYPES],
            value=list(DEFAULT_TYPES),
            id="type-filter-checkbox",
            className="st-type-list",
        ),
        dbc.Switch(id="junk-mode-switch", label="Space junk mode", value=False, className="st-junk-switch"),
        html.P("Almost all rocket bodies and debris are inactive, so most show only with Inactive ticked. "
               "Space junk mode does this for you.", className="st-type-note"),
        dcc.Store(id="status-before-junk", data=None),
    ], className="st-type-filter")

"""
Object type filter (roadmap 3.3a; D-016): payloads, rocket bodies and debris as switches in the panel, plus "Space junk
mode" for both junk types. They go into the filter spec as an `object_type in [...]` clause (Q5), which drives the
globe and the other views. UNKNOWN is never offered, so it stays hidden (D-011).

Each switch shows "matching / total" (roadmap 3.3b, Q6): objects of that type matching the other filters, out of all
of that type. A switched-on type that matches nothing gets a hint saying why (Q2).

Almost every rocket body and debris object is Inactive in the data (all but 6 of 12,398 on 21 Nov 2026), so the note
under the switches says so; Space junk mode also sets status to All (owner, 26 Nov 2026; app/callbacks/callback_filters.py).
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import OBJECT_TYPES
from app.helper.helper__filter_display import TYPE_LABELS

SWATCH = {"PAYLOAD": "st-swatch-payload", "ROCKET BODY": "st-swatch-rocket", "DEBRIS": "st-swatch-debris"}


def type_options(summary):
    """The type switches' options for a panel summary (helper__filter_display.panel_summary): swatch, name and
    "matching / total"."""
    return [{
        "label": html.Span([
            html.Span(className=f"st-swatch {SWATCH[t]}"),
            html.Span(TYPE_LABELS[t], className="st-type-name"),
            html.Span([html.Strong(f"{summary['matches'][t]:,}", className="st-type-match"),
                       f" / {summary['totals'][t]:,}"], className="st-type-total"),
        ], className="st-type-option"),
        "value": t,
    } for t in OBJECT_TYPES]


def type_hints(summary):
    return [html.P(h, className="st-type-hint") for h in summary["hints"]]


def create_type_filter(summary, types, shown=True):
    """
    @param summary: (dict) panel_summary() for the starting values
    @param types: (list) the types switched on at the start
    @param shown: (bool) False hides the section (still in the page, so its callbacks keep working). Only the globe can
                  draw rocket bodies and debris: the Plotly views draw the app CSV, which holds payloads only, so with
                  the globe off the switches would do nothing (#83)
    @return: html.Div with the type checklist (id type-filter-checkbox), the hints (type-hint), the junk switch
             (junk-mode-switch), the note, and the store that remembers the status from before junk mode
             (status-before-junk)
    """
    return html.Div([
        html.Label("Object Type", className="st-lbl"),
        dcc.Checklist(
            options=type_options(summary),
            value=list(types),
            id="type-filter-checkbox",
            className="st-type-list",
        ),
        html.Div(type_hints(summary), id="type-hint", role="status"),
        dbc.Switch(id="junk-mode-switch", label="Space junk mode", value=False, className="st-junk-switch"),
        html.P("Almost all rocket bodies and debris are inactive, so most show only with status Inactive or All. "
               "Space junk mode does this for you.", className="st-type-note"),
        dcc.Store(id="status-before-junk", data=None),
    ], id="type-filter", className="st-type-filter", hidden=not shown)

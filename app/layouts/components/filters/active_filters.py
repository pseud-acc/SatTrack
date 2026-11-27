"""
Active-filter chips and "Clear all" (roadmap 3.3b, D-044). One chip per control that narrows what's shown, labelled
with the field's label from the schema (D-030). A chip's remove button widens its control (status All, every orbit,
nothing selected, the whole year range); "Clear all" restores the values the tracker opens with (D-049). The type
chip has no remove button: the type switches set it.

The chips have fixed ids (chip-<name>, its text chip-<name>-text, its button chip-x-<name>) and are hidden when not
needed, so the callbacks need no pattern-matching ids.
"""

from dash import html
from app.helper.helper__filter_display import CHIPS


def _chip(name, text):
    parts = [html.Span(text or "", id=f"chip-{name}-text")]
    if name != "types":
        parts.append(html.Button("×", id=f"chip-x-{name}", n_clicks=0, className="st-chip-x",
                                 title="Remove this filter", **{"aria-label": "Remove this filter"}))
    return html.Span(parts, id=f"chip-{name}", className="st-chip", hidden=text is None)


def create_active_filters(summary):
    """
    @param summary: (dict) panel_summary() for the starting values
    @return: html.Div with the chips and the "Clear all" button (filter-clear-all, hidden while nothing differs from
             the defaults)
    """
    return html.Div([
        html.Div([
            html.Label("Active filters", className="st-lbl"),
            html.Button("Clear all", id="filter-clear-all", n_clicks=0, className="st-clear-all",
                        hidden=not summary["changed"]),
        ], className="st-chips-head"),
        html.Div([_chip(name, summary["chips"][name]) for name in CHIPS], className="st-chips"),
    ], className="st-active-filters")

"""
The live match count at the top of the panel (roadmap 3.3b, D-044, Q4): "16,576 of 32,652 objects", worked out on
the server from the same control values as the filter spec, so it is right on every tab and with the globe off.
"""

from dash import html


def count_children(summary, globe=True):
    """"N of M objects" with the globe on. With it off the views can draw payloads only (the type switches are hidden,
    #83), so the total is the payloads: "N of M payloads"."""
    total, noun = (summary["total"], "objects") if globe else (summary["totals"]["PAYLOAD"], "payloads")
    return [html.Span(f"{summary['count']:,}", className="st-count-n"),
            html.Span(f"of {total:,} {noun}", className="st-count-of")]


def create_match_count(summary, globe=True):
    """@param summary: (dict) panel_summary() for the starting values
    @param globe: (bool) the globe is on (app.core.viewer.viewer_state)"""
    return html.Div(count_children(summary, globe), id="filter-count", className="st-count", role="status",
                    **{"aria-live": "polite"})

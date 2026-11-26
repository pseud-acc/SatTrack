"""
The live match count at the top of the panel (roadmap 3.3b, D-044, Q4): "16,576 of 32,652 objects", worked out on
the server from the same control values as the filter spec, so it is right on every tab and with the globe off.
"""

from dash import html


def count_children(summary):
    return [html.Span(f"{summary['count']:,}", className="st-count-n"),
            html.Span(f"of {summary['total']:,} objects", className="st-count-of")]


def create_match_count(summary):
    """@param summary: (dict) panel_summary() for the starting values"""
    return html.Div(count_children(summary), id="filter-count", className="st-count", role="status",
                    **{"aria-live": "polite"})

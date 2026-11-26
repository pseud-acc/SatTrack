"""
The tracker's credits line (D-044, roadmap 3.12). The big "Live Tracker" heading is gone: the page name is in the top
bar, and the data's update time moved there too (app/layouts/layout_navbar.py). The credits stay on the page, in a
slim footer under the views, with Space-Track's conjunction caution (CLAUDE.md: public outputs carrying Space-Track
fields cite USSPACECOM and keep the caution).
"""

from dash import html


def create_credits():
    """
    The tracker footer: data credits and the conjunction caution.

    Returns:
        html.Footer: credits component
    """
    return html.Footer(_source_credit(), className="st-credits", id="tracker-credits")


def _source_credit():
    """Credit line for the data shown (Space-Track's terms require the USSPACECOM citation and the caution)."""
    return [
        html.Span("Orbital data: "),
        html.A("USSPACECOM via Space-Track.org", href="https://www.space-track.org/", target="_blank",
               rel="noopener noreferrer"),
        html.Span(". Public element sets must not be used for conjunction (collision) assessment. "),
        html.Span("Launch, owner and mission details: "),
        html.A("GCAT (J. McDowell, planet4589.org)", href="https://planet4589.org/space/gcat/", target="_blank",
               rel="noopener noreferrer"),
        html.Span(", CC-BY."),
    ]

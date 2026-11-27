"""
Orbit type filter (LEO, MEO, GEO, GSO, HEO): a segmented control where any combination can be on (roadmap 3.3b,
Q3). Each button has its own info card on hover (owner, 26 Nov 2026); the (i) card is a short explainer that
points to them (owner, 27 Nov 2026).

The cards describe the rule the pipeline actually uses to sort objects (pipeline/transform/macros, helper__classify_
orbit_class: by orbital period, eccentricity and inclination from Space-Track GP), not altitude bands.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from app.helper.helper__app_data import DEFAULT_ORBITS

# Orbit class -> (name, indicative height, how SatTrack decides it). Periods: 128 min; one sidereal day ~1,436 min (GSO:
# 97-103% of it). Heights are above the equator for a circular orbit with that period (Kepler's third law, WGS 84):
# 128 min -> 2,035 km; 0.97 / 1 / 1.03 day -> 34,937 / 35,785 / 36,624 km. Indicative only: the
# class is decided by the period, not the height.
ORBIT_HELP = {
    "LEO": ("Low Earth orbit", "up to about 2,000 km",
            "Goes round the Earth in under 128 minutes, on a near-circular path. E.g. the ISS."),
    "MEO": ("Medium Earth orbit", "about 2,000 to 35,000 km",
            "Takes from 128 minutes to just under a day per orbit."),
    "GEO": ("Geostationary orbit", "about 35,800 km",
            "Goes round once a day on a circular path over the equator, so it stays above one spot on the ground."),
    "GSO": ("Geosynchronous orbit", "about 35,000 to 36,600 km on average",
            "Goes round about once a day (23.2 to 24.7 hours) but isn't geostationary: tilted or slightly oval, so it "
            "drifts back and forth over the ground."),
    "HEO": ("Highly elliptical orbit", "varies: low at one end, far out at the other",
            "Any other orbit: long, stretched paths that swing far out from the Earth and back."),
}


def _option(orbit):
    # The label is a span with an id so its own tooltip can target it (the input itself is visually hidden).
    return {"label": html.Span(orbit, id=f"orbit-opt-{orbit}"), "value": orbit}


def _card(orbit):
    name, height, rule = ORBIT_HELP[orbit]
    return dbc.Tooltip(html.Div([html.Strong(f"{orbit}: {name}"), html.Br(), html.Em(f"Height: {height}"), html.Br(),
                                 rule], className="st-tip-body"),
                       target=f"orbit-opt-{orbit}", placement="bottom", delay={"show": 150, "hide": 50})


def create_orbit_filter(options):
    """
    @param options: (dict) the sidebar options (options["orbit"]: the five classes in display order)
    @return: html.Div with the label and (i) card, the segmented control (id orbit-filter-checkbox) and a hover card
             per button
    """
    return html.Div([
        html.Label([
            "Orbit Type ",
            html.I(className="st-icon st-icon-info", id="orbit-info-icon")
        ], className="st-lbl"),
        # A short explainer; each button's own card has the definition (owner, 27 Nov 2026: the (i) card repeated them)
        dbc.Tooltip(html.Div([
            "Orbit types group objects by how long they take to go round the Earth and the shape of their path.",
            html.Br(), html.Em("Hover over an orbit for its definition."),
        ], className="st-tip-body"), target="orbit-info-icon", placement="right"),
        dcc.Checklist(
            options=[_option(orbit) for orbit in options["orbit"]],
            value=list(DEFAULT_ORBITS),   # every orbit class (owner, 26 Nov 2026; roadmap 3.3a)
            id="orbit-filter-checkbox",
            className="st-seg st-seg-multi mb-3",
            inline=True
        ),
        *[_card(orbit) for orbit in options["orbit"]],
    ])

# layout_home.py
"""
The home page ("Overview"; D-059, owner's choices of 28 Nov 2026 from the home page mockups).

- Hero: the number of tracked objects as the headline and the agreed sub-line, both figures read from the data
  (app/core/catalogue_summary.py), one action (open the tracker) and quick links to well-known objects present in
  the data (they open the tracker with the object selected, D-024).
- The catalogue at a glance (S1): six index tiles, each with one headline figure, its top three entries as plain
  numbers and a link to its Explore page.
- "From SatTrack's records": figures only this catalogue's status, ownership and data-quality fields can give
  (shown only when object_detail is published).
- What sets SatTrack apart, in six short points; then where the data comes from.
No figure on this page is typed in.
"""
from dash import html, dcc

from app.core.state import get_app_data
from app.core.catalogue_summary import VIEWS

TRACKER = "/sat_visualisation"


def n(value):
    return f"{int(value):,}"


def _top(view, count=3):
    return [html.Li([html.Span(e["name"], className="st-tile-name"), html.Span(n(e["count"]), className="st-tile-n")])
            for e in view["entries"][:count]]


def _tile(key, figure, label, view=None, note=None):
    """One index tile: a headline figure, what it counts, the top three (or a note) and a link to its page."""
    body = [html.Div(n(figure), className="st-tile-figure"), html.Div(label, className="st-tile-label")]
    if view is not None:
        body.append(html.Ul(_top(view), className="st-tile-top"))
    if note:
        body.append(html.P(note, className="st-tile-note"))
    if key in VIEWS:
        body.append(dcc.Link(f"Explore {VIEWS[key][0].lower()}", href=f"/explore/{key}", className="st-tile-link"))
    else:   # the junk tile: the tracker is where they show
        body.append(html.A("Open the tracker", href=TRACKER, className="st-tile-link"))
    return html.Article(body, className="st-tile", id=f"tile-{key}")


def _point(title, text):
    return html.Div([html.H3(title, className="st-home-card-title"), html.P(text, className="st-home-card-text")],
                    className="st-home-card")


def hero(summary):
    t = summary["totals"]
    quick = [html.A(o["name"], href=f"{TRACKER}#v=1&sat={o['satcat_id']}", className="st-chip-link")
             for o in summary["well_known"]]
    return html.Section([
        html.H1(f"{n(t['tracked'])} tracked objects in Earth orbit.", className="st-home-title", id="home-title"),
        html.P(f"{n(t['working'])} working satellites, alongside inactive satellites, rocket bodies and debris. "
               "Explore them live on one globe, by owner, mission, constellation and orbit.",
               className="st-home-lede", id="home-lede"),
        html.Div([
            html.A("Open the tracker", href=TRACKER, className="btn btn-primary btn-lg st-home-cta",
                   id="get-started-button"),
            dcc.Link("Explore the catalogue", href="/explore", className="st-home-second"),
        ], className="st-home-actions"),
        html.Div([html.Span("Go straight to:", className="st-quick-label"), *quick], className="st-quick",
                 id="home-quick") if quick else None,
    ], className="st-home-hero")


def tiles(summary):
    t, v = summary["totals"], summary["views"]
    return html.Section([
        html.H2("The catalogue at a glance", className="st-home-h2"),
        html.Div([
            _tile("orbits", t["working"], "working satellites", v["orbits"]),
            _tile("constellations", v["constellations"]["groups"], "constellations", v["constellations"]),
            _tile("systems", v["systems"]["groups"], "satellite systems", v["systems"]),
            _tile("operators", v["operators"]["groups"], "operators", v["operators"]) if v["operators"]["groups"]
            else _tile("countries", v["countries"]["groups"], "owner countries", v["countries"]),
            _tile("missions", v["missions"]["groups"], "kinds of mission", v["missions"]),
            _tile("junk", t["rocket_bodies"] + t["debris"], "rocket bodies and pieces of debris",
                  note=f"{n(t['rocket_bodies'])} rocket bodies and {n(t['debris'])} pieces of debris, "
                       f"with {n(t['inactive'])} inactive satellites. Space junk mode shows them all."),
        ], className="st-tiles"),
    ], className="st-home-section", id="home-tiles")


def records_strip(summary):
    r = summary["records"]
    if not r:
        return None

    def item(value, text):
        return html.Li([html.Strong(n(value)), f" {text}"])
    return html.Section([
        html.H2("From SatTrack's records", className="st-home-h2"),
        html.Ul([
            item(r["still_transmitting"], "satellites have stopped operating but still transmit"),
            item(r["several_owners"], "objects have more than one owner on record"),
            item(r["estimated_mass"], "masses are marked as estimates"),
            item(r["uncertain_match"], "catalogue matches are marked as uncertain"),
        ], className="st-records"),
    ], className="st-home-section", id="home-records")


def create_dash_layout(app):
    summary = get_app_data()["data"]["summary"]
    return html.Div([
        hero(summary),
        tiles(summary),
        records_strip(summary),
        html.Section([
            html.H2("More than dots on a globe", className="st-home-h2"),
            html.Div([
                _point("Everyone behind it", "Every owner, operator, manufacturer and launch agency, each with its role."),
                _point("Sources you can cite", "Every fact shows its source and date. Copy a citation or a link to any object."),
                _point("Uncertainty marked", "Estimated masses, approximate dates and uncertain matches are marked where they show."),
                _point("Working, or still transmitting", "Whether a satellite still operates, has stopped but still transmits, or is silent, with the dates."),
                _point("Constellations and systems", "How many satellites a network has, how many are active, and which one you are looking at."),
                _point("The junk too", "Rocket bodies and debris beside working satellites, in the list and on the globe."),
            ], className="st-points"),
        ], className="st-home-section", id="home-why"),
        html.Section([
            html.H2("Where the data comes from", className="st-home-h2"),
            html.P(["Orbits from USSPACECOM via Space-Track.org, details from GCAT, groupings from CelesTrak, updated "
                    "daily. ", dcc.Link("Sources and credits", href="/sources", className="st-home-link")]),
        ], className="st-home-section", id="home-sources"),
    ], className="st-home")

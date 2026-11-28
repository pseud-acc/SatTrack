"""
The Explore, Sources and FAQ pages (D-059; owner's N2 choice of 28 Nov 2026: "less is more": Overview, Tracker, an
Explore menu, Sources and FAQ).

- Explore: a summary page and one page per view (constellations, satellite systems, operators, countries, missions,
  orbits): the working satellites ranked by that view, every figure from app/core/catalogue_summary.py. The sub-menu
  on each page is the same list as the top bar's Explore menu.
- Sources: where each kind of data comes from, the required credits and the conjunction caution.
- FAQ: six short answers, each a <details>. The wording comes from the app's own published definitions (the orbit
  rules of the filter panel, D-047 for constellations and systems, D-053 for junk, GCAT's own phrases for operating
  and transmitting), never from general knowledge.
"""
from dash import html, dcc

from app.core.state import get_app_data
from app.core.catalogue_summary import VIEWS
from app.layouts.components.filters.orbit_filter import ORBIT_HELP

TRACKER = "/sat_visualisation"
DOCS = "https://pseud-acc.github.io/SatTrack/"
ROWS = 25          # entries listed per Explore page; the rest are counted in a line under the table


def n(value):
    return f"{int(value):,}"


def explore_links():
    """(key, title, href, description) for the summary and each view: the Explore menu's items, in order."""
    out = [("summary", "Summary", "/explore", "The catalogue at a glance.")]
    out += [(key, title, f"/explore/{key}", text) for key, (title, text, _) in VIEWS.items()]
    return out


def _subnav(active):
    return html.Nav([dcc.Link(title, href=href, className="st-subnav-link" + (" is-active" if key == active else ""))
                     for key, title, href, _ in explore_links()],
                    className="st-subnav", **{"aria-label": "Explore"})


def _page(title, lede, *children, page_id):
    return html.Div([html.Section([html.H1(title, className="st-page-title"),
                                   html.P(lede, className="st-home-lede") if lede else None],
                                  className="st-page-head"), *children], className="st-home st-page", id=page_id)


def _table(view, noun, working):
    shown = view["entries"][:ROWS]
    rest = view["entries"][ROWS:]
    rows = [html.Tr([html.Td(str(i + 1), className="st-rank"), html.Td(e["name"]),
                     html.Td(n(e["count"]), className="st-num"),
                     html.Td(f"{100 * e['count'] / working:.1f}%" if working else "", className="st-num")])
            for i, e in enumerate(shown)]
    table = html.Table([
        html.Thead(html.Tr([html.Th("#", className="st-rank"), html.Th(noun.capitalize()),
                            html.Th("Working satellites", className="st-num"),
                            html.Th("Share", className="st-num")])),
        html.Tbody(rows)], className="st-rank-table")
    more = (html.P(f"And {n(len(rest))} more, with {n(sum(e['count'] for e in rest))} working satellites between them.",
                   className="st-tile-note") if rest else None)
    return html.Div([table, more], className="st-table-wrap")


def create_explore_layout(view_key=None):
    """The Explore summary (view_key None or unknown) or one view's page."""
    summary = get_app_data()["data"]["summary"]
    totals, views = summary["totals"], summary["views"]
    if view_key not in VIEWS:
        cards = [html.Article([
            html.H2(title, className="st-home-card-title"),
            html.P(text, className="st-home-card-text"),
            html.Div(f"{n(views[key]['groups'])} with working satellites", className="st-tile-label"),
            html.Ul([html.Li([html.Span(e["name"], className="st-tile-name"),
                              html.Span(n(e["count"]), className="st-tile-n")]) for e in views[key]["entries"][:5]],
                    className="st-tile-top"),
            dcc.Link(f"All {title.lower()}", href=f"/explore/{key}", className="st-tile-link"),
        ], className="st-tile", id=f"explore-card-{key}") for key, (title, text, _) in VIEWS.items()
            if views[key]["groups"]]
        return _page("Explore the catalogue",
                     f"{n(totals['working'])} working satellites, grouped six ways. Counts are of working "
                     "satellites: payloads with status Active.",
                     _subnav("summary"), html.Div(cards, className="st-tiles"), page_id="page-explore")
    title, text, noun = VIEWS[view_key]
    view = views[view_key]
    if not view["groups"]:
        body = html.P("This view needs the detail dataset, which isn't available right now.", className="st-tile-note")
    else:
        body = _table(view, noun, totals["working"])
    covered = (f"{n(view['satellites'])} of {n(totals['working'])} working satellites have "
               f"{'an' if noun[0] in 'aeiou' else 'a'} {noun} on record.")
    return _page(title, text, _subnav(view_key), html.P(covered, className="st-covered", id="explore-covered"), body,
                 html.P(["Filter the globe by these in the ", html.A("tracker", href=TRACKER, className="st-home-link"),
                         "."], className="st-tile-note"),
                 page_id=f"page-explore-{view_key}")


def create_sources_layout():
    def source(title, who, href, text):
        return html.Article([html.H2(title, className="st-home-card-title"),
                             html.P([html.A(who, href=href, target="_blank", rel="noopener noreferrer",
                                            className="st-home-link"), ". ", text], className="st-home-card-text")],
                            className="st-home-card")
    return _page(
        "Sources and credits", "SatTrack takes its data only from the original publishers and updates it daily.",
        html.Div([
            source("Orbits", "USSPACECOM via Space-Track.org", "https://www.space-track.org/",
                   "Element sets for every tracked object, and each object's type."),
            source("Details", "GCAT (J. McDowell, planet4589.org)", "https://planet4589.org/space/gcat/",
                   "Owners, operators, manufacturers, launches, missions and status. CC BY 4.0."),
            source("Groupings", "CelesTrak (Dr T.S. Kelso)", "https://celestrak.org/",
                   "Constellation and satellite system groups, completed from GCAT."),
            source("Positions", "satellite.js", "https://github.com/shashwatak/satellite-js",
                   "Worked out in your browser from the element sets with the SGP4 model (MIT). The globe is CesiumJS "
                   "(Apache-2.0) with Natural Earth imagery (public domain)."),
        ], className="st-points"),
        html.Section([
            html.H2("Using the data", className="st-home-h2"),
            html.P("Public element sets must not be used for conjunction (collision) assessment.", id="sources-caution"),
            html.P(["Each selected object in the tracker has a Cite button that copies a citation with its sources and "
                    "dates. Column definitions and lineage are in the ",
                    html.A("data documentation", href=DOCS, target="_blank", rel="noopener noreferrer",
                           className="st-home-link"), "."]),
        ], className="st-home-section"),
        page_id="page-sources")


def faq_items():
    """(question, answer children). Kept as data so tests can check each answer against its source."""
    orbit = [html.Li([html.Strong(f"{name} ({code}): "), rule]) for code, (name, _, rule) in ORBIT_HELP.items()]
    return [
        ("What do the orbit types mean?",
         [html.P("SatTrack classes each orbit by how long one lap takes, not by height:"), html.Ul(orbit)]),
        ("What is the difference between a constellation and a satellite system?",
         [html.P("A constellation is near-identical satellites working together, such as Starlink. A satellite system "
                 "is different satellites working together on one service, such as GPS; a satellite can belong to "
                 "several, for example a weather satellite that also carries a search-and-rescue repeater.")]),
        ("Why are rocket bodies and debris always inactive?",
         [html.P("An object's type comes from Space-Track and its status from GCAT. SatTrack treats every object "
                 "Space-Track classes as a rocket body or debris as Inactive, whatever the status record says, so "
                 "junk never shows as a working satellite.")]),
        ("What does \"still transmitting\" mean?",
         [html.P("GCAT records two things separately: whether a satellite is believed to be still operating, and "
                 "whether it is believed to be still transmitting. A satellite can stop operating and keep "
                 "transmitting; SatTrack shows both, with the dates GCAT gives.")]),
        ("How do I cite SatTrack's data?",
         [html.P(["Select an object in the tracker and press Cite: it copies a one-line citation naming the sources "
                  "and their dates, with a link that opens the object. The publishers to credit are listed under ",
                  dcc.Link("Sources", href="/sources", className="st-home-link"), "."])]),
        ("How accurate are the positions?",
         [html.P("Positions are worked out with the SGP4 model from the latest public element set for each object, "
                 "updated daily; the tracker shows how old each element set is. They are good for seeing where "
                 "things are, and must not be used for conjunction (collision) assessment.")]),
    ]


def create_faq_layout():
    return _page("Questions and answers", None,
                 html.Div([html.Details([html.Summary(q, className="st-faq-q"), html.Div(a, className="st-faq-a")],
                                        className="st-faq", id=f"faq-{i + 1}") for i, (q, a) in enumerate(faq_items())],
                          className="st-faqs"),
                 page_id="page-faq")

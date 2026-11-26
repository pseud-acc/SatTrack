"""
"More filters" (roadmap 3.3b, D-044): owner, launch vehicle, purpose and launch year as rows that show their current
value ("Any", "France +2", "1990–2005") and open their control. The rows are native <details> elements, so opening
one needs no callback and works with the keyboard.
"""

from dash import dcc, html
from app.core import filter_spec
from app.helper.helper__app_data import LAUNCH_YEAR_MIN, launch_year_bounds
from app.helper.helper__filter_display import ROWS


def _row(name, summary, control):
    return html.Details([
        html.Summary([
            html.Span(filter_spec.label(ROWS[name]), className="st-row-name"),
            html.Span(summary, id=f"more-{name}-summary", className="st-row-value"),
            html.I(className="st-icon st-icon-chevron-down st-row-chevron"),
        ], className="st-row-head"),
        html.Div(control, className="st-row-body"),
    ], className="st-row", id=f"more-{name}")


def _dropdown(options, placeholder, cid):
    return dcc.Dropdown(options=options, multi=True, value=[], placeholder=placeholder, id=cid,
                        className="st-adv-dropdown")


def create_advanced_filters(options, summary):
    """
    @param options: (dict) the dropdowns' options (helper__app_data.create_data_filters)
    @param summary: (dict) panel_summary() for the starting values (the rows' summaries)
    @return: html.Div with the four rows
    """
    rows = summary["rows"]
    return html.Div([
        html.Label("More filters", className="st-lbl"),
        _row("owner", rows["owner"],
             _dropdown(options["owner"], "Select owners...", "owner-filter-multi-dropdown")),
        _row("launchvehicle", rows["launchvehicle"],
             _dropdown(options["launchvehicle"], "Select launch vehicles...", "launchvehicle-filter-multi-dropdown")),
        _row("purpose", rows["purpose"],
             _dropdown(options["purpose"], "Select purposes...", "purpose-filter-multi-dropdown")),
        # Fixed bounds, independent of the data: 1958 to the current year (UTC), read each time the page is built,
        # so the slider reaches this year's launches without a code change. It starts on the whole range (3.3a).
        _row("year", rows["year"], html.Div([
            dcc.RangeSlider(
                min=LAUNCH_YEAR_MIN,
                max=launch_year_bounds()[1],
                step=1,
                value=launch_year_bounds(),
                marks={},
                allow_direct_input=False,   # Dash 4: no number boxes; the row shows the range
                id="launchyear-filter-slider",
                tooltip={"placement": "top", "always_visible": False},
                className="custom-range-slider"
            ),
            # The slider's ends, under the track (the dragged value shows in the bubble and the row's summary)
            html.Div([html.Span(str(LAUNCH_YEAR_MIN)), html.Span(str(launch_year_bounds()[1]))],
                     className="st-year-ends"),
        ], className="st-year-track")),
    ], className="st-more mb-3")

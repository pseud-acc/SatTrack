"""
The views' tabs build their contents only when opened (D-052; owner, 27 Nov 2026: every tab was rendered at once,
so a phone ran the Plotly 3D scene and the 2D map's WebGL behind the globe).

- 2D View: the map is built each time the tab opens and removed when it closes, with its 3 s timer on only while
  it's open. A closed tab holds no map, no WebGL context and no timer; Plotly's script loads on the first open.
- List View: built by callback_table only while open, and not resent when the filters haven't changed.
"""
from dash.dependencies import Input, Output, State

from app.core.state import get_app_data
from app.helper.helper__app_data import filter_satellite_data
from app.helper.helper__plot_display import create_2d_figure, create_2d_scatter_plot
from app.layouts.components.visualizations.viz_2d import create_2d_body


def register(app):
    app_data = get_app_data()
    df = app_data['data']['satcat_df']
    filter_table = app_data['filter']['table']
    layout_2d = app_data['viz_2d']['layout']

    @app.callback(
        Output("tab-2d-body", "children"),
        Output("2d-viz-interval-component", "disabled"),
        Input("sat-viz-tabs", "active_tab"),
        State("filter-spec", "data"),
    )
    def mount_2d(tab, spec):
        if tab != "2d-viz":
            return [], True
        dff, time_now, _ = filter_satellite_data(df, filter_table, spec)
        return create_2d_body(create_2d_figure(layout_2d, create_2d_scatter_plot(dff, time_now))), False

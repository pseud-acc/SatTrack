"""

This module defines functions to assist with generating plots

Example:

        $ python helper__plot_display.py

Function:
    filter_df:
Todo:
    *

-- Functions required:
    This module ingest plot data and creates plotly figures for display
    - Create 3d layout
    - Create 3d surface of earth
    - Create 3d hover config
    - Create 3d orbit path hover config
    - Create 3d scatter of satellites (incl. annotations)
    - Update 3d camera position
    - Create 3d orbit path lines
    - Create 2d layout
    - Create 2d hover config
    - Create 2d scatter of satellites
    - Generate hover activity colours

    Structure: 
        - Generic functions
        - 3d plot functions
            - Scatter plot functions
            - Orbit path functions
        - 2d plot functions


"""

## Imports
# Standard libraries
import zlib
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import sys

# Internal scripts
sys.path.append("../../")
from app.helper.helper__constants import (_radius_earth__c, _len_3d_viz_axis__c)
from app.helper.helper__satellite_position import (compute_satloc, lla_to_xyz, sphere)
from app.helper.helper__app_data import generate_orbital_path
from app.styles.styles_sat_visualisations import (colorscale, colours, colorscale_marker, colorscale_markerpath)

# Generic functions
def hover_activity_colours(status):
    """
    Generate hover activity colours based on satellite status.
    @param status: (str) Satellite status
    @return: (str) Colour code
    """
    return colours['markerpath1'] if status == "Active" else colours['markerpath0']

# 3D plot functions
def create_3d_layout():
    """
    Create 3D plot layout.
    @return: (Layout) Plotly 3D layout object
    """
    axis_range = [-_len_3d_viz_axis__c-_radius_earth__c, _radius_earth__c+_len_3d_viz_axis__c]
    layout_3d = go.Layout(scene=dict(aspectratio=dict(x=1, y=1, z=1),
                        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        zaxis=dict(showgrid=False, zeroline=False, visible=False, range=axis_range),
                        camera=dict(up=dict(x=0, y=0, z=1),
                                    center=dict(x=0, y=0, z=0),
                                    eye=dict(x=0.035, y=-0.2,z=0.12),
                                    projection=dict(type='perspective')
                                   )),
                      #uirevision='true',
                      showlegend=False,
                      paper_bgcolor="black",
                      margin=dict(l=0, r=0, t=0, b=0))
    return layout_3d

def create_3d_surface(img):
    """
    Create 3D surface of the Earth.
    @param img: (array) Image data for Earth's surface
    @return: (Surface) Plotly Surface object
    """
    x,y,z = sphere(_radius_earth__c,img)
    surf_3d = go.Surface(x=x, y=y, z=z,
                      surfacecolor=img,
                      colorscale=colorscale,
                      showscale=False,
                      hoverinfo="none")            
    return surf_3d

# --- 3D hover: one shared template; each point sends only its values (customdata + position text) ---

HOVER_LABEL_3D = dict(
    namelength=0,
    font_family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    font_size=12,
    font_color="white",
    bgcolor="rgba(13, 15, 18, 0.95)",
    bordercolor="#0dcaf0",
    align="left"
)

# customdata columns, in order, for the hover template
CUSTOMDATA_3D = ["ObjectName", "SatCatId", "status_colour", "Status", "OrbitClass", "LaunchYear", "Owner"]

_HOVER_HEAD_3D = (
    '<b style="font-size: 14px; background: linear-gradient(90deg, #00ff88 0%, #0dcaf0 100%); '
    '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
    'background-clip: text; color: #0dcaf0;">%{customdata[0]}</b><br>'
    '<span style="color: rgba(173, 181, 189, 0.6);">━━━━━━━━━━━━━━━</span><br>'
    '<b>ID:</b> <span style="color: rgba(255, 255, 255, 0.9);">%{customdata[1]}</span><br>'
    '<b>Status:</b> <span style="color: %{customdata[2]};">●</span> '
    '<span style="color: %{customdata[2]};">%{customdata[3]}</span><br>'
    '<b>Orbit:</b> <span style="color: rgba(255, 255, 255, 0.9);">%{customdata[4]}</span><br>'
)

# Satellite markers: the full label; the position (changes every tick) comes from `text`
HOVER_TEMPLATE_3D = (
    _HOVER_HEAD_3D +
    '<b>Launch:</b> <span style="color: rgba(255, 255, 255, 0.9);">%{customdata[5]}</span><br>'
    '<b>Owner:</b> <span style="color: rgba(255, 255, 255, 0.9);">%{customdata[6]}</span><br>'
    '<span style="color: rgba(173, 181, 189, 0.6);">━━━━━━━━━━━━━━━</span><br>'
    '<b>Position:</b><br>'
    '<span style="color: rgba(108, 117, 125, 0.8); font-size: 11px;">  '
    'Lat: %{text}km</span>'
    '<extra></extra>'
)


def scatter_3d_customdata(dff):
    """
    Per-satellite hover values (the columns in CUSTOMDATA_3D), sent once per full redraw.

    @param dff: (DataFrame) filtered satellites
    @return: (list) one list of values per satellite
    """
    data = dff[["ObjectName", "SatCatId", "Status", "OrbitClass", "LaunchYear", "Owner"]].copy()
    data["status_colour"] = np.where(data["Status"] == "Active", colours['markerpath1'], colours['markerpath0'])
    return data[CUSTOMDATA_3D].values.tolist()


def scatter_3d_position_text(dff):
    """
    Position part of the hover label, "<lat>° | Lon: <lon>° | Alt: <alt>" (the template adds "Lat: " and "km").

    @param dff: (DataFrame) satellites with lat, lon, alt
    @return: (list) one string per satellite
    """
    return (dff["lat"].round(2).astype(str) + "° | Lon: " + dff["lon"].round(2).astype(str) + "° | Alt: " +
            dff["alt"].round().astype(int).astype(str)).tolist()


def scatter_3d_xyz(dff):
    """
    Marker positions in km, rounded to 0.1 km (far below a pixel at any zoom).

    @param dff: (DataFrame) satellites with xp, yp, zp
    @return: (tuple) x, y, z lists
    """
    return tuple(dff[c].astype(np.float64).round(1).tolist() for c in ("xp", "yp", "zp"))


def satellite_ids_signature(dff):
    """
    Short fingerprint of which satellites are shown, in order. A timer tick may send positions only when it
    matches the figure already in the browser; otherwise the hover values would no longer line up.

    @param dff: (DataFrame) filtered satellites
    @return: (str) "<count>:<crc32 of the ids>"
    """
    ids = np.ascontiguousarray(dff["SatCatId"].to_numpy(dtype=np.int64))
    return f"{len(ids)}:{zlib.crc32(ids.tobytes()):08x}"


def create_3d_scatter_plot(dff, sat_status_encoded):
    """
    Create 3D scatter plot of satellites. Trace index 1 in the figure (handle_orbit_click relies on it).

    @param dff: (DataFrame) Filtered satellite data
    @param sat_status_encoded: (array) Encoded satellite status
    @return: (Scatter3d) 3D scatter plot object
    """
    x, y, z = scatter_3d_xyz(dff)
    scatter_3d = go.Scatter3d(x=x, y=y, z=z,
                                mode="markers", showlegend=False,
                                marker=dict(color=np.where(dff["Status"] == "Active", 1, 0), cmin=0, cmax=1,
                                            colorscale=colorscale_marker, opacity=0.65, size=2.5,
                                            line=dict(color=sat_status_encoded,
                                                    colorscale=colorscale_marker, width=0.01,
                                                    cmin=0, cmax=1)),
                                customdata=scatter_3d_customdata(dff),
                                text=scatter_3d_position_text(dff),
                                hovertemplate=HOVER_TEMPLATE_3D,
                                hoverlabel=HOVER_LABEL_3D
                                )
    return scatter_3d

def create_3d_figure(layout_3d, surf_3d, scatter_3d=None):
    """
    Create 3D figure from layout, surface, and scatter plot.

    @param layout_3d: (Layout) 3D plot layout
    @param surf_3d: (Surface) 3D surface of the Earth
    @param scatter_3d: (Scatter3d) 3D scatter plot of satellites (optional)

    @return: (Figure) Plotly Figure object with 3D visualization
    """
    
    if scatter_3d is not None:
        fig_3d = go.Figure(data=[surf_3d, scatter_3d], layout=layout_3d)
    else:
        fig_3d = go.Figure(data=[surf_3d], layout=layout_3d)

    return fig_3d

def annotation_3d_text(dff, time_now):
    """
    Text of the 3D figure's annotation: position time and satellite counts.

    @param dff: (DataFrame) Filtered satellite data
    @param time_now: (datetime) Current time
    @return: (str) annotation text
    """
    return ('<i><span style="font-size: clamp(8px, 2vw, 12px);">Satellite position as at: ' +
            time_now.strftime("%H:%M:%S, %d/%m/%Y") + '</span></i> <br>' +
            '<i><span style="font-size: clamp(8px, 2vw, 12px);">Number of active/inactive satellites shown: ' +
            "/".join([str(sum(dff.Status == "Active")), str(sum(dff.Status == "Inactive"))]) +
            ' (' + str(dff.shape[0]) + ' in total)' + '</span></i>')


def annotate_3d_figure(fig_3d, dff, time_now):
    """
    Add annotations to 3D figure (layout.annotations[0], which timer ticks update in place).

    @param fig_3d: (Figure) 3D figure object
    @param dff: (DataFrame) Filtered satellite data
    @param time_now: (datetime) Current time
    @return: (Figure) Updated 3D figure with annotations
    """
    fig_3d.add_annotation(dict(font=dict(color=colours["atext"], size=10),
                                x=0.005, y=0.99, showarrow=False,
                                text=annotation_3d_text(dff, time_now),
                                textangle=0, xanchor='left', align='left',
                                xref="paper", yref="paper"))
    return fig_3d

def update_3d_camera_view(cam_mem, cam_scene, fig_3d):
    """
    Update 3D camera view based on user interactions.

    @param cam_mem: (dict) Camera memory from dcc.Store
    @param cam_scene: (dict) Camera scene from relayoutData
    @param fig_3d: (Figure) Current 3D figure

    @return: (dict) Updated camera memory
    """
    try:
        cam_scene["scene.camera"]
    except:
        try:
            cam_mem["scene.camera"]
        except:
            fig_3d.update_layout(scene_camera=fig_3d["layout"]["scene"]["camera"])
        else:
            fig_3d.update_layout(scene_camera=cam_mem["scene.camera"])
    else:
        fig_3d.update_layout(scene_camera=cam_scene["scene.camera"])
        cam_mem = cam_scene["scene.camera"]

    return fig_3d, cam_mem

# Orbit path functions
def handle_orbit_click(callback_context, click_data, orbit_list, dff):
    """
    Handle orbit click events and update orbit list.

    @param callback_context: Dash callback context
    @param click_data: (dict) Click data from 3D plot
    @param orbit_list: (list) Current list of orbit IDs
    @param dff: (DataFrame) Filtered satellite dataframe

    @return: (list) Updated list of orbit IDs
    """
    from dash.exceptions import PreventUpdate

    # Get which input triggered the callback
    ctx = callback_context
    input_name = ctx.triggered[0]['prop_id'].split('.')[0]
    input_type = ctx.triggered[0]['prop_id'].split('.')[1]

    # Check and initialize orbit list
    orbit_list_updated = orbit_list
    if input_name == "clear-orbits-btn":
        orbit_list_updated = []

    # Check for input updates - filter change or valid click (i.e. Satellite marker)
    if input_type == "clickData":
        if not click_data:
            raise PreventUpdate
        elif click_data["points"][0]["curveNumber"] != 1:
            raise PreventUpdate

    # Do not update if existing 3d orbit is clicked
    if input_type == "clickData":
        if click_data["points"][0]["curveNumber"] == 1:
            orbit_id = dff.iloc[[click_data["points"][0]["pointNumber"]]]["SatCatId"].values[0]
            if orbit_id in orbit_list_updated:
                raise PreventUpdate            

    # Update orbit list with new orbit if valid click
    if input_type == "clickData":
        if click_data["points"][0]["curveNumber"] == 1:
            orbit_list_updated.append(dff.iloc[[click_data["points"][0]["pointNumber"]]]["SatCatId"].values[0])
            orbit_list_updated = list(set(orbit_list_updated))    

    return orbit_list_updated

def create_orbit_traces(dff, orbit_list, time_now):
    """
    Orbit path traces for the tracked satellites: for each, the path line and an enlarged marker at the current
    position. Every point of a path has the same hover label, so the path sends it once as its template.

    @param dff: (DataFrame) Filtered satellite data
    @param orbit_list: (list) Satellite IDs whose orbits are shown
    @param time_now: (datetime) Current time
    @return: (list) Scatter3d traces, two per tracked satellite still in dff
    """
    traces = []
    for orbit_id in orbit_list:
        if orbit_id in dff["SatCatId"].values:
            d3d = generate_orbital_path(dff[dff["SatCatId"] == orbit_id],
                                720, time_now, True)
            first = d3d.iloc[[0]]
            sat = scatter_3d_customdata(first)[0]
            path_template = _HOVER_HEAD_3D
            for i in range(5):
                path_template = path_template.replace("%{customdata[" + str(i) + "]}", str(sat[i]))
            status_enc = np.where(d3d["Status"] == "Active", 1, 0)
            # Satellite orbital path
            traces.append(go.Scatter3d(x=d3d["xp"].round(1), y=d3d["yp"].round(1), z=d3d["zp"].round(1),
                                    line=dict(color=status_enc, cmin=0, cmax=1,
                                            colorscale=colorscale_markerpath, width=5),
                                    mode="lines", showlegend=False,
                                    hovertemplate=path_template + '<extra></extra>',
                                    hoverlabel=HOVER_LABEL_3D))
            # Oversized plot point for current position in orbital path
            traces.append(go.Scatter3d(x=[round(float(d3d["xp"].iloc[0]), 1)],
                                    y=[round(float(d3d["yp"].iloc[0]), 1)],
                                    z=[round(float(d3d["zp"].iloc[0]), 1)],
                                    marker=dict(color=status_enc[:1],
                                                colorscale=colorscale_markerpath,
                                                cmin=0, cmax=1, opacity=0.65, size=8),
                                    mode="markers", showlegend=False,
                                    customdata=[sat], text=scatter_3d_position_text(first),
                                    hovertemplate=HOVER_TEMPLATE_3D, hoverlabel=HOVER_LABEL_3D))
    return traces


def add_orbit_paths_to_figure(fig_3d, dff, orbit_list, time_now):
    """
    Add orbit paths to 3D figure (traces 2 onwards).

    @param fig_3d: (Figure) 3D figure object
    @param dff: (DataFrame) Filtered satellite data
    @param orbit_list: (list) List of satellite IDs to show orbits for
    @param time_now: (datetime) Current time
    @return: (Figure) Updated 3D figure with orbit paths
    """
    for trace in create_orbit_traces(dff, orbit_list, time_now):
        fig_3d.add_trace(trace)
    return fig_3d



def create_2d_layout():
    """
    Create 2D plot layout.
    @return: (Layout) Plotly 2D layout object
    """
    layout_2d = go.Layout(
        autosize=True,
        # height=500,
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(
            style="white-bg",
            center_lat = 0,
            center_lon = 0,        
            zoom=0,
            bearing=0,
            pitch=0,  
            layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "United States Geological Survey",
                    "source": [
                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                    ]
            }
          ])
    )

    return layout_2d

def create_2d_scatter_hover_label(dff):
    """
    Generate hover configuration for 2D satellite markers.
    @param dff: DataFrame with satellite data
    @return: list of hover labels
    """

    hover_label = ['<b>Lat</b>: ' + round(dff["lat"],2).astype(str) + '&deg;' + '<br>' +
           '<b>Lon</b>: ' + round(dff["lon"],2).astype(str) + '&deg;' + '<br>' +
           '<b>Alt</b>: ' + round(dff["alt"]).astype(int).astype(str) + 'km <br>' +  
           '<b>Datetime (UTC)</b>: ' + dff["Datetime"].astype(str)]
    
    return hover_label

def create_2d_scatter_plot(dff, time_now):
    """
    Create 2D scatter plot of satellites.
    @param dff: (DataFrame) Filtered satellite dataframe
    @param colours: (dict) Colour definitions
    @param time_now: (datetime) Current timestamp
    @return: (Figure) Plotly Figure object with 2D scatter plot
    """

    # Create 2D scatter plot
    if dff.shape[0] == 1:
        d2d = generate_orbital_path(dff, 3600, time_now, False)

        # Generate hover labels
        hover_labels = create_2d_scatter_hover_label(d2d)

        scatter_2d_orbit_path = go.Scattermapbox(lat=d2d["lat"], lon=d2d["lon"],
                                        marker=dict(color=colours["marker1"], opacity=0.1, size=10),
                                        mode="markers", showlegend=False,
                                        hoverlabel=dict(namelength=0), hoverinfo="text",
                                        hovertext=hover_labels[0]
                                        )
        scatter_2d_current_position = go.Scattermapbox(lat=[d2d["lat"][0]], lon=[d2d["lon"][0]],
                                        marker=dict(color=colours["marker2"], opacity=0.6, size=20),
                                        mode="markers", showlegend=False,
                                        hoverlabel=dict(namelength=0), hoverinfo="text",
                                        hovertext='<b>Current Position</b>' + '<br>' +
                                                    hover_labels[0][0]
                                        )
        return [scatter_2d_current_position, scatter_2d_orbit_path]

    else:
        return []

def create_2d_figure(layout_2d, scatter_plots=[]):
    """
    Create 2D figure from layout and scatter plots.
    @param layout_2d: (Layout) 2D plot layout
    @param scatter_plots: (list) List of 2D scatter plots (optional)
    @return: (Figure) Plotly Figure object with 2D visualization
    """
    
    # Handle case with no scatter plots
    if len(scatter_plots) == 0:
        fig_2d = go.Figure(data=go.Scattermapbox(
            lat=[0], lon=[0],
            marker_opacity = 0,
            mode = "markers",
            showlegend = False,
            hoverinfo='none',
            hoverlabel=dict(namelength=0)    
        ),
        layout=layout_2d)
    else:
        fig_2d = go.Figure(data=scatter_plots, layout=layout_2d)

    return fig_2d

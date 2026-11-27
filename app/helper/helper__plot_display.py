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
    - Create 2d layout
    - Create 2d hover config
    - Create 2d scatter of satellites
    - Generate hover activity colours

    Structure: 
        - Generic functions
        - 2d plot functions


"""

## Imports
# Standard libraries
import plotly.graph_objs as go
import sys

# Internal scripts
sys.path.append("../../")
from app.helper.helper__app_data import generate_orbital_path
from app.styles.styles_sat_visualisations import colours

# 2D plot functions (the Plotly 3D view was removed: the Cesium globe replaces it, D-052)
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

#!/usr/bin/env python

"""

This module defines app settings - colour, styles.

Example:

        $ python app_settings.py

Attributes:

Todo:
    * 

"""
## Colours - text, tabs, plots
colours = {
    "btext" : "#dae0e3", #grey - app button text
    "ttext" : "#dae9f2", #greyish-blue - app title text
    "atext" : "#ffffff", #white - 3d plot annotation text
    "marker0" :"#c0c9cc", #grey - marker for inactive satellites    
    "marker1" : "#e00000", #red - marker for Satellites    
    "marker2" : "#49fcf3", #cyan - marker for current satellite position
    "markeredge" : "#b84949", #greyish-red - marker edge for Satellites
    "markerpath" : "#59ff00", #bright green - path for satellite in 3d
    "markerpath0" : "#dee2e3", #light grey - path for inactive satellite in 3d
    "markerpath1" : "#FF3131", #bright red - path for active satellite in 3d    
    "dropdownbox" : "#dae0e3", #light greyish blue - background for dropdown box
    "tab": "#7c919c" #greyish-blue - tab background
}

## Colour scale to convert 2d greyscale of Earth surface to coloured texture
colorscale =[[0.0, 'rgb(30, 59, 117)'],

             [0.1, 'rgb(46, 68, 21)'],
             [0.2, 'rgb(74, 96, 28)'],
             [0.3, 'rgb(115,141,90)'],
             [0.4, 'rgb(122, 126, 75)'],

             [0.6, 'rgb(122, 126, 75)'],
             [0.7, 'rgb(141,115,96)'],
             [0.8, 'rgb(223, 197, 170)'],
             [0.9, 'rgb(237,214,183)'],

             [1.0, 'rgb(255, 255, 255)']]

## Colour scale for 3d markers
colorscale_marker =[[0.0, colours["marker0"]],
                    [1.0, colours["marker1"]]]

## Fontsize
fontsize = {
    "checkbox" : "17px", #checkbox text
    "dropdown" : "17px", #dropdown menu text
    "slider" : "25px" #range slider text
}

## Tab Styles
tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '2px solid ' + colours["ttext"],
    'padding': '6px',
    'fontWeight': 'bold'
}
tab_selected_style = {
    'borderTop': '1px solid ' + colours["ttext"],
    'borderBottom': '1px solid ' + colours["ttext"],
    'backgroundColor': colours["tab"],
    'color': colours["ttext"],
    'padding': '6px'
}


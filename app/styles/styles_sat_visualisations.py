"""
Script containing styles and colours for python dash and plotly objects
in satellite visualisation tabs
"""

# Colours

## Colours - text, tabs, plots
colours = {
    "btext": "#f8f9fa",  # Lighter text for better contrast
    "ttext": "#00d4ff",  # Brighter blue for headers
    "atext": "#ffffff",
    "marker0": "#6c757d",  # Better contrast inactive marker
    "marker1": "#ff4444",  # Brighter active marker
    "marker2": "#00ff88",  # Better visibility current position
    "markeredge" : "#bab6b7", #greyish-red - marker edge for Satellites
    "markerpath" : "#59ff00", #bright green - path for satellite in 3d
    "markerpath0" : "#b5bdbf", #light grey - path for inactive satellite in 3d
    "markerpath1" : "#e00000", #bright red - path for active satellite in 3d
    "dropdownbox": "#2b3035",  # Darker dropdown background
    "tab": "#1a1d21",
    "hboxbg0": "#495057",
    "hboxbg1": "#dc3545",
    "hboxtx0": "#ffffff",
    "hboxtx1": "#ffffff"
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

## Colour scale for 3d path
colorscale_markerpath =[[0.0, colours["markerpath0"]],
                    [1.0, colours["markerpath1"]]]


# Styles

## Fontsize
fontsize = {
    "heading": "clamp(1.5rem, 5vw, 2.5rem)",  # Responsive heading
    "sub-heading": "clamp(1rem, 3vw, 1.25rem)",
    "sub-sub-heading": "clamp(0.75rem, 2vw, 0.875rem)",
    "checkbox": "1rem",
    "dropdown": "0.875rem",
    "slider": "0.875rem"
}

## Tab Styles
_tabs__style = {
    'height': '44px'
}

_tab__style = {
    'borderBottom': '2px solid ' + colours["ttext"],
    'padding': '6px',
    'fontWeight': 'bold'
}

_tab_selected__style = {
    'borderTop': '1px solid ' + colours["ttext"],
    'borderBottom': '1px solid ' + colours["ttext"],
    'backgroundColor': colours["tab"],
    'color': colours["ttext"],
    'padding': '6px'
}


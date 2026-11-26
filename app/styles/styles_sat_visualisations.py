"""
Script containing styles and colours for python dash and plotly objects
in satellite visualisation tabs
"""

from app.styles.tokens import TOKENS

# Colours

## Plotly figure colours, from the design tokens (assets/03_tokens.css via app/styles/tokens.py; 3.12 step 4).
## Status follows the globe's default colouring (owner, 24 Nov 2026): soft red active, grey inactive.
colours = {
    "atext": TOKENS["st-fg"],              # 3D annotation text
    "marker0": TOKENS["st-inactive"],      # inactive satellite
    "marker1": TOKENS["st-active"],        # active satellite
    "marker2": TOKENS["st-accent-hi"],     # selected satellite's current position (2D)
    "markerpath0": TOKENS["st-inactive"],  # orbit path, inactive satellite (3D)
    "markerpath1": TOKENS["st-active"],    # orbit path, active satellite (3D)
}

# The Earth's surface texture below is geography, not interface colour, so it keeps its own scale.
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

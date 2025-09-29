"""
Script containing styles and colours for python dash and plotly objects
in satellites explained tab
"""

## Styles

# Page
_main_page__style = {
        'width': '80%',
        'margin': 'auto',
        'max-width': '1200px'
}

# Tab header title
_tab_header__style = {
                "text-align": "center",
                "font-size": "3.2em",
                "margin-bottom": "40px",
                "color": "#0091ea",
                "font-weight": "700",
                "text-shadow": "0px 1px 2px rgba(0, 0, 0, 0.1)"
            }

# Tab content
_tab_content__style = {
    "margin-left": "230px",
    "padding-top": "20px"
}

# Navigation bar
_navbar__style = {
            "position": "fixed",
            "top": "70px",  # Adjusted for header height
            "left": "0",
            "height": "calc(100% - 70px)",
            "width": "200px",
            "padding": "20px",
            "border-radius": "15px",
            "background-color": "rgba(255, 255, 255, 0.08)",  # Slightly visible background
            "border-right": "1px solid rgba(0, 145, 234, 0.2)",
            "box-shadow": "2px 0px 10px rgba(0, 0, 0, 0.05)",
            "z-index": "100",  # Ensure it stays above content
            "backdrop-filter": "blur(5px)"  # Modern blur effect for depth
}

# Navigation bar tabs
_navbar_tabs__style = {
            "padding": "15px",
            "display": "block",
            "color": "#0091ea",
            "font-weight": "500"
}

# Text sub-section
_text_section_child__style = {
    "display": "flex",
    "flex-wrap": "wrap",
    "align-items": "flex-start",
    "gap": "30px",
    "padding": "20px"
}

# Main text section
_text_section_parent__style = {
    "text-align": "justify",
    # "background": "linear-gradient(145deg, #ffffff, #f5f9ff)",
    "background-color": "rgba(255, 255, 255, 0.08)",  # Slightly visible background
    "border-radius": "15px",
    "padding": "25px",
    "box-shadow": "0 4px 12px rgba(0, 145, 234, 0.1)"
}

# Section title style
_section_title__style = {
    "margin-bottom": "25px",
    "font-size": "2.2em",
    "font-weight": "600",
    "color": "#bdc3c7",  # Match header color
    "border-bottom": "2px solid rgba(0, 145, 234, 0.2)",  # Subtle underline
    "padding-bottom": "8px",
    "width": "fit-content"  # Only as wide as the text
}

# Section text
_text__style = {
    "flex": "1",
    "padding": "1px",
    "font-size": "1em",  # Slightly larger font for better readability
    "color": "#d7dbdd",  # Darker text color for better contrast
    "line-height": "1.7",  # Increased line height
    "letter-spacing": "0.01em"  # Slight letter spacing for improved readability
}

# Section text paragraphs
_paragraph__style = {
    "margin-bottom": "16px",
    "font-size": "1em",
    "line-height": "1.7",
    "color": "#797d7f",
    "text-align": "justify",
    "hyphens": "auto"
}

# Section image
_image__style = {
    "padding": "0",  # Removed padding to maximize image size
    "box-shadow": "0 6px 16px rgba(0, 0, 0, 0.15)",  # Enhanced shadow for images
    "border-radius": "12px",
    "max-width": "100%",
    "height": "auto",
    "margin-bottom": "15px",
    "transition": "transform 0.3s ease",  # Add transition for hover effect
    "border": "2px solid #f0f0f0"  # Subtle border around images
}

# Section image caption
_image_caption__style = {
    "text-align": "center",
    "font-style": "italic",
    "font-size": "0.85em",
    "color": "#555",  # Slightly lighter color for captions
    "max-width": "95%",
    "margin": "0 auto 20px auto"  # Center caption with margins
}

# Section image box
_image_box__style = {
    "flex": "1",
    "align-self": "flex-start",
    "padding-right": "30px",  # Increased spacing between image and text
    "width": "35%",  # Slightly wider image section
    "min-width": "250px"  # Ensure minimum width on smaller screens
}

# Section image alignment
_image_box_alignment__style = {
    "text-align": "center"
}

# Refined fact button section
_fact_section__style = {
    "min-height": "160px",  # Reduced minimum height
    "display": "flex",
    "flex-wrap": "wrap",  # Allow wrapping on smaller screens
    "justify-content": "space-between",  # Evenly distribute buttons
    "gap": "15px",  # Gap between buttons
    "margin-bottom": "50px",
    "margin-top": "30px"
}

# Collapsed fact buttons
_fact_button_collapsed__style = {
    "height": "auto",  # Auto height based on content
    "min-height": "110px",  # Minimum height for consistency
    "flex": "1",  # Flex grow to distribute space
    "min-width": "200px",  # Minimum width for smaller screens
    "max-width": "24%",  # Maximum width to maintain 4 buttons per row
    "font-size": "1.1em",
    "font-weight": "500",  # Semi-bold text
    "background-color": "rgba(0, 145, 234, 0.08)",  # Light blue background matching header
    "color": "#0091ea",  # Button text color matches header
    "border": "1px solid rgba(0, 145, 234, 0.3)",  # Subtle border
    "border-radius": "12px",
    "padding": "15px 10px",
    "cursor": "pointer",
    "transition": "all 0.2s ease-in-out",  # Smooth transition for hover
}

# Expanded fact button
_fact_button_expanded__style = {
    'textAlign': 'center',
    'font-size': '0.9em',
    'background-color': 'rgba(0, 145, 234, 0.9)',
    'color': 'white',
    'border': 'none',
    'padding': '10px',
    'border-radius': '12px',
    'height': 'auto',
    'min-height': '130px',
    'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.2)',
    'transition': 'all 0.3s ease',
    'overflow': 'auto'
}

# Fact button expanded text - callback
_fact_button_expanded_text__style = {
    'textAlign': 'left',
    'font-size': '0.95em',
    'line-height': '1.4',
    'padding': '5px'
}

# Fact button expanded title - callback
_fact_button_title__style = {
    "font-weight": "600",
    "display": "block"
}

# Fact button expanded launch details - callback
_fact_button_launch_detail__style = {
    "font-size": "0.8em",
    "margin-top": "5px",
    "opacity": "0.8"
}

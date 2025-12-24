"""
Reusable template for content sections with image, text, and interactive buttons.
"""

from dash import html
import dash_bootstrap_components as dbc
from app.styles.styles_sat_explained import (
    _image__style, _paragraph__style, _fact_button_collapsed__style
)


def create_section_with_buttons(section_id, title, image_src, image_caption,
                                 paragraphs, buttons_title, button_configs,
                                 modal_id, button_color="info"):
    """
    Create a reusable content section with image, paragraphs, and interactive buttons.

    Args:
        section_id (str): HTML section ID
        title (str): Section title
        image_src (str): Path to section image
        image_caption (str): Image caption text
        paragraphs (list): List of paragraph text strings
        buttons_title (str): Title above buttons row
        button_configs (list): List of dicts with button configs (id, title)
        modal_id (str): Base ID for modal components
        button_color (str): Bootstrap color for buttons

    Returns:
        html.Section: Complete section component
    """
    # Create button row
    button_row = dbc.Row([
        dbc.Col([
            dbc.Button(
                config["title"],
                id=config["id"],
                color=button_color,
                outline=True,
                className="w-100 mb-2",
                style={**_fact_button_collapsed__style}
            )
        ], md=6, lg=3, className="mb-2")
        for config in button_configs
    ])

    # Create modal
    modal = dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id=f"{modal_id}-modal-title")),
        dbc.ModalBody(id=f"{modal_id}-modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id=f"close-{modal_id}-modal", className="ms-auto")
        )
    ], id=f"{modal_id}-modal", size="lg", is_open=False)

    # Create section
    return html.Section(id=section_id, children=[
        dbc.Card([
            dbc.CardHeader([
                html.H3(title, className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    # Image column
                    dbc.Col([
                        html.Img(src=image_src,
                                 style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                        html.P(image_caption,
                               className="text-muted small mt-2",
                               style={'textAlign': 'center', 'width': '100%'})
                    ], style={'textAlign': 'center'}),

                    # Text column
                    dbc.Col([
                        *[html.P(para, style={**_paragraph__style}) for para in paragraphs]
                    ], md=7)
                ]),

                html.Hr(className="my-4"),

                html.H5(buttons_title, className="mb-3"),
                button_row,

                modal
            ])
        ], className="mb-4 shadow-sm")
    ])


def create_simple_section(section_id, title, image_src, image_caption,
                          paragraphs, extra_content=None):
    """
    Create a simple content section with image and paragraphs (no buttons).

    Args:
        section_id (str): HTML section ID
        title (str): Section title
        image_src (str): Path to section image
        image_caption (str): Image caption text
        paragraphs (list): List of paragraph text strings
        extra_content: Optional additional content to add after paragraphs

    Returns:
        html.Section: Complete section component
    """
    content = [
        dbc.Card([
            dbc.CardHeader([
                html.H3(title, className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    # Image column
                    dbc.Col([
                        html.Img(src=image_src,
                                 style={**_image__style, 'width': '100%', 'maxWidth': '400px'}),
                        html.P(image_caption,
                               className="text-muted small mt-2",
                               style={'textAlign': 'center', 'width': '100%'})
                    ], style={'textAlign': 'center'}),

                    # Text column
                    dbc.Col([
                        *[html.P(para, style={**_paragraph__style}) for para in paragraphs]
                    ], md=7)
                ])
            ] + ([html.Hr(className="my-4"), extra_content] if extra_content else []))
        ], className="mb-4 shadow-sm")
    ]

    return html.Section(id=section_id, children=content)

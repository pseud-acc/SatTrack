"""
Ownership section component for satellite applications page.
"""

from dash import html
import dash_bootstrap_components as dbc
from app.layouts.components.sat_applications.section_template import create_simple_section


def create_ownership_section():
    """
    Create the satellite ownership section.

    Returns:
        html.Section: Ownership section component
    """
    paragraphs = [
        "Satellites are owned by a diverse range of entities, reflecting the global "
        "nature of space activity. Government agencies, such as NASA in the United States "
        "and the European Space Agency (ESA), lead in satellite launches for national security, "
        "scientific research, and environmental monitoring. Their satellites support vital"
        " projects,  like climate studies and space exploration, ensuring national and "
        "international interests are met.",

        "Private companies have rapidly emerged as key players in satellite ownership. "
        "SpaceX, for example, operates a growing constellation of communication satellites as "
        "part of its Starlink program, aimed at providing global internet coverage. OneWeb and "
        "other private firms contribute similarly, using satellites to support industries "
        "ranging from telecommunications to Earth observation.",

        "Additionally, international collaborations, such as the European Union's Copernicus "
        "program, highlight efforts to manage and share satellite data globally. These "
        "partnerships benefit all by supporting projects related to disaster management, "
        "agriculture, and environmental conservation.",

        "The ownership of satellites underscores a dynamic mix of public and private entities, "
        "each contributing to the rapidly expanding capabilities of satellite technology "
        "and its impact on modern life."
    ]

    # Create ownership distribution chart
    extra_content = html.Div([
        html.P("Distribution by ownership type (example data):", className="mb-2 small text-muted"),
        dbc.Progress([
            dbc.Progress(value=35, color="primary", bar=True, children="Commercial 35%"),
            dbc.Progress(value=30, color="info", bar=True, children="Government 30%"),
            dbc.Progress(value=20, color="success", bar=True, children="Military 20%"),
            dbc.Progress(value=15, color="warning", bar=True, children="Academic 15%")
        ], className="mb-4", style={"height": "30px"})
    ])

    return create_simple_section(
        section_id="owners",
        title="Satellite Ownership",
        image_src="/assets/images/copernicus_programme.jpg",
        image_caption="Satellites are owned by governments, companies, and international organizations.",
        paragraphs=paragraphs,
        extra_content=extra_content
    )

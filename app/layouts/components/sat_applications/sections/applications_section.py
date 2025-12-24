"""
Applications section component for satellite applications page.
"""

from app.layouts.components.sat_applications.section_template import create_section_with_buttons
from app.content.content_buttons import fact_data


def create_applications_section():
    """
    Create the satellite applications section.

    Returns:
        html.Section: Applications section component
    """
    paragraphs = [
        "Satellites play a crucial role in various domains, serving purposes that extend from "
        "environmental monitoring to global communication. Earth observation satellites, situated "
        "in Low Earth Orbit (LEO), capture high-resolution images aiding in disaster response, "
        "climate studies, and tracking environmental changes like the effects of global warming. "
        "Communication satellites, typically positioned in Geostationary Orbit (GEO), facilitate "
        "seamless global connectivity, supporting telecommunications, broadcasting, and internet "
        "services.",

        "The choice of orbit is pivotal to a satellite's function. LEO satellites offer "
        "frequent revisits for real-time observation, while GEO satellites provide continuous "
        "coverage ideal for communication. Medium Earth Orbit (MEO) satellites, like those in "
        "the GPS constellation, strike a balance for navigation. High Earth Orbit (HEO) and "
        "polar orbits cater to specialized missions.",

        "The James Webb Space Telescope, positioned in a unique "
        "orbit, has revolutionized astronomy by making groundbreaking discoveries, including "
        "finding exoplanets with life-supporting molecules, massive galaxies in the infant "
        "universe, the earliest supermassive black holes, and complex molecules in primordial "
        "galaxies.",

        "Satellite usage has dynamically evolved, notably with mega-constellations like "
        "Starlink and OneWeb deploying LEO satellites for global broadband internet access. "
        "Smaller satellites, known as CubeSats, leverage advancements in miniaturization and "
        "cost-effectiveness, fostering innovation in research and technology."
    ]

    button_configs = [
        {"id": "sat-purpose-btn-1", "title": fact_data["purpose"]["btn-1"]["button_title"]},
        {"id": "sat-purpose-btn-2", "title": fact_data["purpose"]["btn-2"]["button_title"]},
        {"id": "sat-purpose-btn-3", "title": fact_data["purpose"]["btn-3"]["button_title"]},
        {"id": "sat-purpose-btn-4", "title": fact_data["purpose"]["btn-4"]["button_title"]}
    ]

    return create_section_with_buttons(
        section_id="applications",
        title="Satellite Applications",
        image_src="/assets/images/jwst.jpg",
        image_caption="Modern satellites serve diverse purposes from communications to climate monitoring.",
        paragraphs=paragraphs,
        buttons_title="Key Applications",
        button_configs=button_configs,
        modal_id="purpose",
        button_color="success"
    )

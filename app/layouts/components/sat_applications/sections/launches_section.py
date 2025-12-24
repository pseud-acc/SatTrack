"""
Launch systems section component for satellite applications page.
"""

from app.layouts.components.sat_applications.section_template import create_section_with_buttons
from app.content.content_buttons import fact_data


def create_launches_section():
    """
    Create the launch systems section.

    Returns:
        html.Section: Launch systems section component
    """
    paragraphs = [
        "Launching a satellite demands precise planning and execution. Satellites travel to launch sites in specialized containers that shield these sensitive instruments during transport. Upon arrival, technicians perform final assembly and testing before the critical payload integration phase—where the satellite is securely fastened to the rocket's adapter. The satellite is then enclosed within the rocket's fairing, a protective aerodynamic shell that shields it from the extreme forces and temperatures encountered during ascent through the atmosphere.",

        "Launch vehicles like SpaceX's Falcon 9 and Arianespace's Ariane 5 generate tremendous thrust to overcome Earth's gravitational pull. Engineers select rockets based on the satellite's mass and destination orbit. Communication satellites bound for Geostationary Orbit (GEO) at 35,786 km (22,236 miles) require powerful rockets with multiple stages, while Earth observation satellites destined for Low Earth Orbit (LEO) need less energy to reach their 300-1,200 km altitudes. Regardless of destination, rockets must accelerate to approximately 28,000 km/h (17,500 mph) to achieve orbit.",

        "Launch economics significantly influence satellite deployment strategies. Current costs range from approximately $2,700 per kilogram to LEO on SpaceX's partially reusable Falcon 9 to around $20,000 per kilogram on smaller vehicles like Rocket Lab's Electron. These figures represent a dramatic reduction from historical costs that often exceeded $50,000 per kilogram before reusable rocket technology.",

        "Once the rocket reaches space, the fairing separates to expose the satellite, and precisely calculated engine burns position the spacecraft in its target orbit. After deployment, the satellite unfolds solar arrays and communication antennas, then uses onboard thrusters for final orbital adjustments. This intricate choreography of engineering and physics transforms years of planning into operational reality."
    ]

    button_configs = [
        {"id": "sat-launches-btn-1", "title": fact_data["launches"]["btn-1"]["button_title"]},
        {"id": "sat-launches-btn-2", "title": fact_data["launches"]["btn-2"]["button_title"]},
        {"id": "sat-launches-btn-3", "title": fact_data["launches"]["btn-3"]["button_title"]},
        {"id": "sat-launches-btn-4", "title": fact_data["launches"]["btn-4"]["button_title"]}
    ]

    return create_section_with_buttons(
        section_id="launches",
        title="Getting to Orbit",
        image_src="/assets/images/iridium_fairing.jpg",
        image_caption="Rocket launches deliver satellites to their designated orbits.",
        paragraphs=paragraphs,
        buttons_title="Launch Systems",
        button_configs=button_configs,
        modal_id="launches",
        button_color="warning"
    )

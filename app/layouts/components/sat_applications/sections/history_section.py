"""
History section component for satellite applications page.
"""

from app.layouts.components.sat_applications.section_template import create_section_with_buttons
from app.content.content_buttons import fact_data


def create_history_section():
    """
    Create the satellite history section.

    Returns:
        html.Section: History section component
    """
    paragraphs = [
        "Satellites boast a captivating history, originating with the concept of artificial "
        "satellites orbiting the Earth. The notion was initially proposed by the science "
        "fiction writer Arthur C. Clarke in 1945. However, it wasn't until the Soviet Union's "
        "historic launch of Sputnik 1 on October 4, 1957, that the space age truly commenced. "
        "Sputnik 1, meaning 'satellite' or 'companion' in Russian, was the world's first "
        "artificial Earth satellite. It was a sphere with four external radio antennas, "
        "broadcasting radio pulses that could be received on Earth.",

        "This groundbreaking achievement marked the beginning of human-made objects orbiting "
        "our planet and kicked off the space race between the United States and the Soviet Union, "
        "each striving for achievements in space exploration and satellite technology.",

        "In the early years, satellites were primarily used for scientific research and"
        " national security. The United States launched the first communication satellite, Echo 1, in 1960, while the "
        "Soviet Union focused on scientific and reconnaissance satellites. Over time, satellites "
        "evolved in terms of size, usage, and ubiquity.",

        "Today, we rely on a multitude of satellites for communication, navigation (GPS), Earth observation, "
        "and various scientific purposes. Satellites have become integral to our daily lives, enabling "
        "global connectivity and providing valuable data for scientific research and"
        " environmental monitoring."
    ]

    button_configs = [
        {"id": "sat-history-btn-1", "title": fact_data["history"]["btn-1"]["button_title"]},
        {"id": "sat-history-btn-2", "title": fact_data["history"]["btn-2"]["button_title"]},
        {"id": "sat-history-btn-3", "title": fact_data["history"]["btn-3"]["button_title"]},
        {"id": "sat-history-btn-4", "title": fact_data["history"]["btn-4"]["button_title"]}
    ]

    return create_section_with_buttons(
        section_id="history",
        title="A Brief History of Satellites",
        image_src="/assets/images/sputnik.jpg",
        image_caption="Sputnik 1 - The first artificial satellite, launched by the Soviet Union in 1957.",
        paragraphs=paragraphs,
        buttons_title="Notable Milestones",
        button_configs=button_configs,
        modal_id="history",
        button_color="info"
    )

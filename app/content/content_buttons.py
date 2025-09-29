"""
Script containing titles and content for buttons in "satellites explained" tab
"""

# Define the facts data - centralized for all buttons to reduce repetition
fact_data = {
    "history": {
        "btn-1": {
            "sat_name": "Sputnik 1",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1957-001B",
            "launch_date": "1957",
            "fact_1": "Orbited the Earth every 96 minutes",
            "fact_2": "Radio transmitter broadcasted globally",
            "fact_3": "Remained in orbit until 4th January 1958",
            "button_title": "First Satellite?"
        },
        "btn-2": {
            "sat_name": "Voyager 1",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1977-084A",
            "launch_date": "1977",
            "fact_1": "Travelled over 23 billion km from Earth",
            "fact_2": "First human-made object to enter interstellar space",
            "fact_3": "Still transmits data back to Earth",
            "button_title": "Furthest Satellite?"
        },
        "btn-3": {
            "sat_name": "International Space Station (ISS)",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1998-067A",
            "launch_date": "1998",
            "fact_1": "108 metres long from end-to-end",
            "fact_2": "Assembly has required 40+ missions",
            "fact_3": "Has been visited by over 260 astronauts",
            "button_title": "Largest Satellite?"
        },
        "btn-4": {
            "sat_name": "Kalamsat-V2",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2019-006B",
            "launch_date": "2019",
            "fact_1": "Weighs only 1.25kg and has a radio comms system",
            "fact_2": "Primarily built from 3D printed parts",
            "fact_3": "Designed and built by Space Kidz India",
            "button_title": "Smallest Satellite?"
        }
    },
    "purpose": {
        "btn-1": {
            "sat_name": "Hubble Space Telescope",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1998-067A",
            "launch_date": "1990",
            "fact_1": "Named after astronomer Edwin Hubble",
            "fact_2": "Determined universe's expansion rate",
            "fact_3": "Discovered habitable exoplanets",
            "button_title": "Hubble Space Telescope"
        },
        "btn-2": {
            "sat_name": "Starlink Constellation",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2019-006B",
            "launch_date": "2019",
            "fact_1": "Deployed by SpaceX for global internet coverage",
            "fact_2": "6,000+ satellites in constellation",
            "fact_3": "Enabled military communications in conflict zones",
            "button_title": "Starlink Constellation"
        },
        "btn-3": {
            "sat_name": "GOES Series",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1957-001B",
            "launch_date": "1975",
            "fact_1": "4 Satellites in constellation - operated by NOAA",
            "fact_2": "Monitors Earth weather and atmospheric conditions",
            "fact_3": "Supports agricultural, maritime, and aviation",
            "button_title": "GOES Series"
        },
        "btn-4": {
            "sat_name": "GPS Satellites",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1977-084A",
            "launch_date": "1978",
            "fact_1": "Developed and operated by US Air Force",
            "fact_2": "32 operational satellites in constellation",
            "fact_3": "Uses atomic clocks for precise timing signals",
            "button_title": "GPS Satellites"
        }
    },
    "launches": {
        "btn-1": {
            "sat_name": "Space Shuttle",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1998-067A",
            "launch_date": "April 12, 1981",
            "fact_1": "First and only winged orbital spacecraft",
            "fact_2": "Deployed 350+ satellites including Hubble",
            "fact_3": "Could launch, repair and retrieve satellites",
            "button_title": "First Reusable Spacecraft"
        },
        "btn-2": {
            "sat_name": "Falcon Series",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=2019-006B",
            "launch_date": "June 4, 2010",
            "fact_1": "Falcon 9: lowest cost launcher at ~$2,700/kg",
            "fact_2": "Falcon Heavy: most powerful at 64 tons to LEO",
            "fact_3": "First to land boosters: 260+ successful returns",
            "button_title": "Lowest Cost Launcher"
        },
        "btn-3": {
            "sat_name": "Ariane Series",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1957-001B",
            "launch_date": "December 24, 1979",
            "fact_1": "Europe's launcher: 45+ years, 300+ flights",
            "fact_2": "Delivered 70% of commercial GEO sats",
            "fact_3": "Ariane 5: 97% success across 117 missions",
            "button_title": "GEO Satellite Specialist"
        },
        "btn-4": {
            "sat_name": "Electron Launcher",
            "nasa_link": "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1977-084A",
            "launch_date": "May 25, 2017",
            "fact_1": "First fully carbon-composite orbital rocket",
            "fact_2": "Uses 3D-printed engines built in just 24 hours",
            "fact_3": "Each rocket built in just 20 days",
            "button_title": "Fastest to Build"
        }
    }
}
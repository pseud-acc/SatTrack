"""

This module defines functions to assist with generating app data

Example:

        $ python helper__table_display.py

Function:
    create_table_mapping: Generate column name mapping for table export
Todo:
    *

"""

TYPE_LABELS = {"PAYLOAD": "Payload", "ROCKET BODY": "Rocket body", "DEBRIS": "Debris"}


def create_table_mapping():
    '''
    Generate column name mapping for table export.
    @return tbl_display_df: (dict) Column name mapping for table display
    '''
    # Every object type, from the objects dataset (owner, 27 Nov 2026: debris and rocket bodies in the list, with
    # their type); the keys are the dataset's field names
    tbl_mapping = {"object_name": "Name", "object_type": "Type", "satcat_id": "SATCAT Number",
                   "operational_status": "Status", "orbit_class": "Orbit", "launch_year": "Year of Launch",
                   "owner_country": "Owner", "lat": "Latitude", "lon": "Longitude", "alt": "Altitude (km)",
                   "Datetime": "Datetime (UTC)"}
    return tbl_mapping

def format_table_data(dff, time_now):
    '''
    Format table data for display.
    @param dff: (DataFrame) Filtered satellite dataframe
    @param time_now: (datetime) Current timestamp
    @return: (tbl_display_output: dict) Formatted table data for display
    '''
    # Get table column mapping
    tbl_column_map = create_table_mapping()

    # Format data. Objects Space-Track hasn't named yet show by their designator (as in the search list)
    dff = dff.copy()
    unnamed = dff["object_name"] == "TBA - TO BE ASSIGNED"
    dff.loc[unnamed, "object_name"] = "Not yet named (" + dff.loc[unnamed, "object_id"].fillna("?") + ")"
    dff["object_type"] = dff["object_type"].map(TYPE_LABELS).fillna(dff["object_type"])
    dff["launch_year"] = dff["launch_year"].astype("Int64")
    dff["lat"] = round(dff["lat"], 2)
    dff["lon"] = round(dff["lon"], 2)
    dff["alt"] = round(dff["alt"]).astype(int)
    dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")

    # Generate table display output
    tbl_display_output = (dff[list(tbl_column_map.keys())].sort_values(by=["object_name", "satcat_id"])
                          .rename(columns=tbl_column_map).astype(object).where(lambda d: d.notna(), None)
                          .to_dict("records"))

    return tbl_display_output
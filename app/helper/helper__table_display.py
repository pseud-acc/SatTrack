"""

This module defines functions to assist with generating app data

Example:

        $ python helper__table_display.py

Function:
    create_table_mapping: Generate column name mapping for table export
Todo:
    *

"""

def create_table_mapping():
    '''
    Generate column name mapping for table export.
    @return tbl_display_df: (dict) Column name mapping for table display
    '''
    tbl_mapping = {"ObjectName":"Satellite Name", "SatCatId": "SATCAT Number", "Status":"Status",
              "OrbitClass":"Orbit", "LaunchYear": "Year of Launch", "Owner":"Owner",
              "lat":"Latitude", "lon":"Longitude", "alt":"Altitude (km)", "Datetime":"Datetime (UTC)"}
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

    # Format data
    dff["lat"] = round(dff["lat"], 2)
    dff["lon"] = round(dff["lon"], 2)
    dff["alt"] = round(dff["alt"]).astype(int)
    dff["Datetime"] = time_now.strftime("%H:%M:%S, %d/%m/%Y")

    # Generate table display output
    tbl_display_output = dff[tbl_column_map].sort_values(by=["ObjectName"]).rename(columns=tbl_column_map).to_dict("records")

    return tbl_display_output
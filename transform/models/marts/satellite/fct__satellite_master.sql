-- One row per object in the Space-Track GP feed, combining Space-Track and GCAT primitives under the
-- decided composite rules (field review 2026-10-25). The app's satellite table.
with cte_int__xsrc__satellite_gcat_matched as (
    select
        satcat_id
        , canonical_satellite_id
        , jcat
        , jcat_link_method
        , flag_gcat_matched
        , object_name
        , object_id
        , object_type
        , object_type_source
        , flag_in_orbit
        , spacetrack_country_code
        , owner_country
        , owner_country_codes
        , owner_country_is_org
        , owner_country_source
        , owner_code
        , launch_date
        , launch_date_source
        , launch_year
        , orbit_class
        , orbit_regime
        , orbital_period
        , inclination
        , eccentricity
        , apoapsis
        , periapsis
        , rcs_size
        , mass_kg
        , flag_mass_estimated
        , dry_mass_kg
        , span_m
        , epoch
        , tle_age_days
        , tle_line_1
        , tle_line_2
        , positions_as_of
        , details_as_of
    from {{ ref('int__xsrc__satellite_gcat_matched') }}
)

, cte_int__jsr__satellite_status as (
    select
        jcat
        , status
        , status_source
        , flag_gcat_descended
        , flag_still_operating
        , flag_still_transmitting
        , end_operation_date
        , end_operation_date_precision
        , end_transmission_date
        , end_transmission_date_precision
        , end_of_life_flag
        , activity_type
        , current_status
        , ownership_class
        , ownership_class_labels
        , mission_category_list
        , mission_category_labels
        , satellite_program
        , satellite_program_family
        , constellation_plane
        , payload_fields_source
        , payload_fields_parent_jcat
    from {{ ref('int__jsr__satellite_status') }}
)

, cte_int__jsr__org_satellite_org_lists as (
    select
        jcat
        , operator_name
        , manufacturer_name
        , owner_org_codes
        , owner_org_names
        , manufacturer_org_codes
        , manufacturer_org_names
    from {{ ref('int__jsr__org_satellite_org_lists') }}
)

, cte_int__jsr__satellite_launch_details as (
    select
        jcat
        , launch_tag
        , launch_datetime
        , launch_datetime_precision
        , site_code
        , site_name
        , site_state
        , site_location_country
        , site_latitude
        , site_longitude
        , lv_type
        , lv_brand
        , lv_family
        , flight_id
        , launch_agency_code
        , launch_agency_name
        , launch_agency_org_codes
        , launch_agency_org_names
        , launch_category
        , flag_catalog_match_uncertain
        , launch_fields_source
    from {{ ref('int__jsr__satellite_launch_details') }}
)

, cte_satellite_master as ( -- joins only: unmatched joins get their documented defaults; owner country spans sources
    select
        sat.canonical_satellite_id
        , sat.satcat_id
        , sat.jcat
        , sat.jcat_link_method
        , sat.flag_gcat_matched
        , sat.object_name
        , sat.object_id
        , sat.object_type
        , sat.object_type_source
        , sat.flag_in_orbit
        -- in the GP feed (so on orbit) while GCAT says it came down
        , coalesce(st.flag_gcat_descended, false) as flag_orbit_conflict
        -- objects without a GCAT status record default to Inactive
        , coalesce(st.status, 'Inactive') as status
        , coalesce(st.status_source, 'default_inactive') as status_source
        , st.flag_still_operating
        , st.flag_still_transmitting
        , st.end_operation_date
        , st.end_operation_date_precision
        , st.end_transmission_date
        , st.end_transmission_date_precision
        , st.end_of_life_flag
        , st.activity_type
        , st.current_status
        , sat.launch_date
        , sat.launch_date_source
        , sat.launch_year
        -- owner country: Space-Track code via boxscore, with the GCAT State rules for CIS and TBD (int__xsrc__satellite_gcat_matched)
        , sat.owner_country
        , sat.owner_country_codes
        , sat.owner_country_is_org
        , sat.owner_country_source
        , sat.spacetrack_country_code
        , sat.owner_code
        -- organisations (every co-org kept as a list for the multi-select filter; empty when unmatched)
        , orgs.operator_name
        , orgs.manufacturer_name
        , coalesce(orgs.owner_org_codes, cast([] as varchar[])) as owner_org_codes
        , coalesce(orgs.owner_org_names, cast([] as varchar[])) as owner_org_names
        , coalesce(orgs.manufacturer_org_codes, cast([] as varchar[])) as manufacturer_org_codes
        , coalesce(orgs.manufacturer_org_names, cast([] as varchar[])) as manufacturer_org_names
        -- launch agencies are launch-level: own launch-log row, else inherited from the launch (see launch_fields_source)
        , coalesce(ld.launch_agency_org_codes, cast([] as varchar[])) as launch_agency_org_codes
        , coalesce(ld.launch_agency_org_names, cast([] as varchar[])) as launch_agency_org_names
        , st.ownership_class
        , coalesce(st.ownership_class_labels, cast([] as varchar[])) as ownership_class_labels
        -- payload-level: own payload record, else inherited from the GCAT Parent chain (see payload_fields_source)
        , st.mission_category_list
        , st.mission_category_labels
        -- launch: own launch-log row, else inherited from the satcat Launch_Tag (see launch_fields_source)
        , ld.launch_tag
        , ld.launch_datetime
        , ld.launch_datetime_precision
        , ld.site_code
        , ld.site_name
        , ld.site_state
        , ld.site_location_country
        , ld.site_latitude
        , ld.site_longitude
        , ld.lv_type
        , ld.lv_brand
        , ld.lv_family
        , ld.flight_id
        , ld.launch_agency_code
        , ld.launch_agency_name
        , ld.launch_category
        , ld.flag_catalog_match_uncertain
        , coalesce(ld.launch_fields_source, 'none') as launch_fields_source
        , st.satellite_program
        , st.satellite_program_family
        , st.constellation_plane
        , coalesce(st.payload_fields_source, 'none') as payload_fields_source
        , st.payload_fields_parent_jcat
        , sat.orbit_class
        , sat.orbit_regime
        , sat.orbital_period
        , sat.inclination
        , sat.eccentricity
        , sat.apoapsis
        , sat.periapsis
        , sat.rcs_size
        , sat.mass_kg
        , sat.flag_mass_estimated
        , sat.dry_mass_kg
        , sat.span_m
        , sat.epoch
        , sat.tle_age_days
        , sat.tle_line_1
        , sat.tle_line_2
        , sat.positions_as_of
        , sat.details_as_of
    from cte_int__xsrc__satellite_gcat_matched as sat
    left join cte_int__jsr__satellite_status as st on st.jcat = sat.jcat
    left join cte_int__jsr__org_satellite_org_lists as orgs on orgs.jcat = sat.jcat
    left join cte_int__jsr__satellite_launch_details as ld on ld.jcat = sat.jcat
)

, cte_final as (
    select
        cast(canonical_satellite_id as varchar) as canonical_satellite_id
        , cast(satcat_id as integer) as satcat_id
        , cast(jcat as varchar) as jcat
        , cast(jcat_link_method as varchar) as jcat_link_method
        , cast(flag_gcat_matched as boolean) as flag_gcat_matched
        , cast(object_name as varchar) as object_name
        , cast(object_id as varchar) as object_id
        , cast(object_type as varchar) as object_type
        , cast(object_type_source as varchar) as object_type_source
        , cast(flag_in_orbit as boolean) as flag_in_orbit
        , cast(flag_orbit_conflict as boolean) as flag_orbit_conflict
        , cast(status as varchar) as status
        , cast(status_source as varchar) as status_source
        , cast(flag_still_operating as boolean) as flag_still_operating
        , cast(flag_still_transmitting as boolean) as flag_still_transmitting
        , cast(end_operation_date as timestamp) as end_operation_date
        , cast(end_operation_date_precision as varchar) as end_operation_date_precision
        , cast(end_transmission_date as timestamp) as end_transmission_date
        , cast(end_transmission_date_precision as varchar) as end_transmission_date_precision
        , cast(end_of_life_flag as varchar) as end_of_life_flag
        , cast(activity_type as varchar) as activity_type
        , cast(current_status as varchar) as current_status
        , cast(launch_date as date) as launch_date
        , cast(launch_date_source as varchar) as launch_date_source
        , cast(launch_year as bigint) as launch_year
        , cast(owner_country as varchar) as owner_country
        , cast(owner_country_codes as varchar[]) as owner_country_codes
        , cast(owner_country_is_org as boolean) as owner_country_is_org
        , cast(owner_country_source as varchar) as owner_country_source
        , cast(spacetrack_country_code as varchar) as spacetrack_country_code
        , cast(owner_code as varchar) as owner_code
        , cast(operator_name as varchar) as operator_name
        , cast(manufacturer_name as varchar) as manufacturer_name
        , cast(owner_org_codes as varchar[]) as owner_org_codes
        , cast(owner_org_names as varchar[]) as owner_org_names
        , cast(manufacturer_org_codes as varchar[]) as manufacturer_org_codes
        , cast(manufacturer_org_names as varchar[]) as manufacturer_org_names
        , cast(launch_agency_org_codes as varchar[]) as launch_agency_org_codes
        , cast(launch_agency_org_names as varchar[]) as launch_agency_org_names
        , cast(ownership_class as varchar) as ownership_class
        , cast(ownership_class_labels as varchar[]) as ownership_class_labels
        , cast(mission_category_list as varchar[]) as mission_category_list
        , cast(mission_category_labels as varchar[]) as mission_category_labels
        , cast(launch_tag as varchar) as launch_tag
        , cast(launch_datetime as timestamp) as launch_datetime
        , cast(launch_datetime_precision as varchar) as launch_datetime_precision
        , cast(site_code as varchar) as site_code
        , cast(site_name as varchar) as site_name
        , cast(site_state as varchar) as site_state
        , cast(site_location_country as varchar) as site_location_country
        , cast(site_latitude as double) as site_latitude
        , cast(site_longitude as double) as site_longitude
        , cast(lv_type as varchar) as lv_type
        , cast(lv_brand as varchar) as lv_brand
        , cast(lv_family as varchar) as lv_family
        , cast(flight_id as varchar) as flight_id
        , cast(launch_agency_code as varchar) as launch_agency_code
        , cast(launch_agency_name as varchar) as launch_agency_name
        , cast(launch_category as varchar) as launch_category
        , cast(flag_catalog_match_uncertain as boolean) as flag_catalog_match_uncertain
        , cast(launch_fields_source as varchar) as launch_fields_source
        , cast(satellite_program as varchar) as satellite_program
        , cast(satellite_program_family as varchar) as satellite_program_family
        , cast(constellation_plane as varchar) as constellation_plane
        , cast(payload_fields_source as varchar) as payload_fields_source
        , cast(payload_fields_parent_jcat as varchar) as payload_fields_parent_jcat
        , cast(orbit_class as varchar) as orbit_class
        , cast(orbit_regime as varchar) as orbit_regime
        , cast(orbital_period as double) as orbital_period
        , cast(inclination as double) as inclination
        , cast(eccentricity as double) as eccentricity
        , cast(apoapsis as double) as apoapsis
        , cast(periapsis as double) as periapsis
        , cast(rcs_size as varchar) as rcs_size
        , cast(mass_kg as double) as mass_kg
        , cast(flag_mass_estimated as boolean) as flag_mass_estimated
        , cast(dry_mass_kg as double) as dry_mass_kg
        , cast(span_m as double) as span_m
        , cast(epoch as timestamp) as epoch
        , cast(tle_age_days as double) as tle_age_days
        , cast(tle_line_1 as varchar) as tle_line_1
        , cast(tle_line_2 as varchar) as tle_line_2
        , cast(positions_as_of as timestamp) as positions_as_of
        , cast(details_as_of as timestamp) as details_as_of
        , {{ helper__audit_fields() }}
    from cte_satellite_master
)

select * from cte_final

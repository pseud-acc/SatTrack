-- App export: the object_detail dataset (object_detail.json; docs/app-data-contract.md, decisions D-010, D-054), what
-- the globe's selection panel shows beyond the objects dataset (roadmap 3.4). The browser fetches it once, on the
-- first selection, and looks records up by satcat_id. One record per object in the objects dataset (the same GP
-- objects with a full element set, so both files have the same keys), with the warehouse's own column names.
-- Descriptive fields from fct__satellite_master (enrichment) through a left join: an object new to the GP feed has
-- a record with null details until enrichment next succeeds.
-- Gaps stay null; lists are always lists, empty when none. Dates are ISO text (JSON has no date type); each
-- GCAT vague date travels with its precision so the panel never shows more precision than GCAT gives.
with cte_fct__gp_elements as (
    select
        satcat_id
        , epoch
        , mean_motion
        , eccentricity
        , inclination
        , ra_of_asc_node
        , arg_of_pericenter
        , mean_anomaly
        , bstar
        , mean_motion_dot
        , mean_motion_ddot
        , rev_at_epoch
        , element_set_no
        , ephemeris_type
        , classification_type
        , orbital_period
    from {{ ref('fct__gp_elements') }}
)

, cte_fct__satellite_master as (
    select
        satcat_id
        , jcat
        , jcat_link_method
        , object_type_source
        , operational_status_source
        , flag_still_operating
        , flag_still_transmitting
        , end_operation_date
        , end_operation_date_precision
        , end_transmission_date
        , end_transmission_date_precision
        , end_of_life_code
        , flag_orbit_conflict
        , owner_country_codes
        , owner_country_source
        , owner_org_codes
        , owner_org_names
        , operator_name
        , manufacturer_org_codes
        , manufacturer_org_names
        , launch_agency_org_codes
        , launch_agency_org_names
        , launch_datetime
        , launch_datetime_precision
        , launch_details_source
        , flag_catalog_match_uncertain
        , site_code
        , site_name
        , site_latitude
        , site_longitude
        , launch_vehicle_type
        , launch_vehicle_family
        , flight_id
        , satellite_program
        , satellite_program_family
        , constellation_plane
        , mission_details_source
        , apoapsis
        , periapsis
        , rcs_size
        , mass_kg
        , flag_mass_estimated
        , dry_mass_kg
        , span_m
        , gcat_updated_at
    from {{ ref('fct__satellite_master') }}
)

-- the objects dataset's scope (app__objects.sql): GP objects with every field a propagator needs
, cte_tracked_objects as (
    select
        satcat_id
    from cte_fct__gp_elements
    where epoch is not null
        and mean_motion is not null
        and eccentricity is not null
        and inclination is not null
        and ra_of_asc_node is not null
        and arg_of_pericenter is not null
        and mean_anomaly is not null
        and bstar is not null
        and mean_motion_dot is not null
        and mean_motion_ddot is not null
        and rev_at_epoch is not null
        and element_set_no is not null
        and ephemeris_type is not null
        and classification_type is not null
        and orbital_period > 0
)

, cte_object_detail as (
    select
        obj.satcat_id
        , sat.jcat
        , sat.jcat_link_method
        , sat.object_type_source
        , sat.operational_status_source
        , sat.flag_still_operating
        , sat.flag_still_transmitting
        , sat.end_operation_date
        , sat.end_operation_date_precision
        , sat.end_transmission_date
        , sat.end_transmission_date_precision
        , sat.end_of_life_code
        , coalesce(sat.flag_orbit_conflict, 0) as flag_orbit_conflict   -- no satellite-mart row: no conflict known
        , sat.owner_country_codes
        , sat.owner_country_source
        , sat.owner_org_codes
        , sat.owner_org_names
        , sat.operator_name
        , sat.manufacturer_org_codes
        , sat.manufacturer_org_names
        , sat.launch_agency_org_codes
        , sat.launch_agency_org_names
        , sat.launch_datetime
        , sat.launch_datetime_precision
        , sat.launch_details_source
        , coalesce(sat.flag_catalog_match_uncertain, 0) as flag_catalog_match_uncertain
        , sat.site_code
        , sat.site_name
        , sat.site_latitude
        , sat.site_longitude
        , sat.launch_vehicle_type
        , sat.launch_vehicle_family
        , sat.flight_id
        , sat.satellite_program
        , sat.satellite_program_family
        , sat.constellation_plane
        , sat.mission_details_source
        , sat.apoapsis
        , sat.periapsis
        , sat.rcs_size
        , sat.mass_kg
        , coalesce(sat.flag_mass_estimated, 0) as flag_mass_estimated
        , sat.dry_mass_kg
        , sat.span_m
        , sat.gcat_updated_at
    from cte_tracked_objects as obj
    left join cte_fct__satellite_master as sat
        on obj.satcat_id = sat.satcat_id
)

, cte_final as (
    select
        cast(satcat_id as bigint) as satcat_id
        , cast(jcat as varchar) as jcat
        , cast(jcat_link_method as varchar) as jcat_link_method
        , cast(object_type_source as varchar) as object_type_source
        , cast(operational_status_source as varchar) as operational_status_source
        , cast(flag_still_operating as integer) as flag_still_operating
        , cast(flag_still_transmitting as integer) as flag_still_transmitting
        , strftime(end_operation_date, '%Y-%m-%dT%H:%M:%S') as end_operation_date
        , cast(end_operation_date_precision as varchar) as end_operation_date_precision
        , strftime(end_transmission_date, '%Y-%m-%dT%H:%M:%S') as end_transmission_date
        , cast(end_transmission_date_precision as varchar) as end_transmission_date_precision
        , cast(end_of_life_code as varchar) as end_of_life_code
        , cast(flag_orbit_conflict as integer) as flag_orbit_conflict
        , cast(coalesce(owner_country_codes, []) as varchar[]) as owner_country_codes
        , cast(owner_country_source as varchar) as owner_country_source
        , cast(coalesce(owner_org_codes, []) as varchar[]) as owner_org_codes
        , cast(coalesce(owner_org_names, []) as varchar[]) as owner_org_names
        , cast(operator_name as varchar) as operator_name
        , cast(coalesce(manufacturer_org_codes, []) as varchar[]) as manufacturer_org_codes
        , cast(coalesce(manufacturer_org_names, []) as varchar[]) as manufacturer_org_names
        , cast(coalesce(launch_agency_org_codes, []) as varchar[]) as launch_agency_org_codes
        , cast(coalesce(launch_agency_org_names, []) as varchar[]) as launch_agency_org_names
        , strftime(launch_datetime, '%Y-%m-%dT%H:%M:%S') as launch_datetime
        , cast(launch_datetime_precision as varchar) as launch_datetime_precision
        , cast(launch_details_source as varchar) as launch_details_source
        , cast(flag_catalog_match_uncertain as integer) as flag_catalog_match_uncertain
        , cast(site_code as varchar) as site_code
        , cast(site_name as varchar) as site_name
        , cast(site_latitude as double) as site_latitude
        , cast(site_longitude as double) as site_longitude
        , cast(launch_vehicle_type as varchar) as launch_vehicle_type
        , cast(launch_vehicle_family as varchar) as launch_vehicle_family
        , cast(flight_id as varchar) as flight_id
        , cast(satellite_program as varchar) as satellite_program
        , cast(satellite_program_family as varchar) as satellite_program_family
        , cast(constellation_plane as varchar) as constellation_plane
        , cast(mission_details_source as varchar) as mission_details_source
        , cast(apoapsis as double) as apoapsis
        , cast(periapsis as double) as periapsis
        , cast(rcs_size as varchar) as rcs_size
        , cast(mass_kg as double) as mass_kg
        , cast(flag_mass_estimated as integer) as flag_mass_estimated
        , cast(dry_mass_kg as double) as dry_mass_kg
        , cast(span_m as double) as span_m
        , strftime(gcat_updated_at, '%Y-%m-%dT%H:%M:%S') as gcat_updated_at
    from cte_object_detail
)

select * from cte_final
order by satcat_id

-- App export: the objects dataset (objects.json; decisions D-009 to D-011, docs/app-data-contract.md), which the
-- browser loads once and propagates itself (Phase 3). One record per tracked object, keyed by satcat_id, with the
-- warehouse's own column names. scripts/export_app_csvs.py wraps the rows in the dataset envelope, validates every
-- record against app/contracts/objects.schema.json and pre-compresses the file.
-- Scope: every object in the GP feed with a full element set, of any type (payloads, rocket bodies, debris and
-- Space-Track's UNKNOWN analyst objects; the UI decides what to show). Elements come from fct__gp_elements
-- (tracking, every run); descriptive fields from fct__satellite_master (enrichment). A left join: an object new to
-- the GP feed appears at once, with null details until enrichment next succeeds.
-- Gaps stay null (no 'Unknown' / -1 placeholders as in the CSV); label lists are always lists, empty when none.
with cte_fct__gp_elements as (
    select
        satcat_id
        , object_id
        , object_name
        , object_type
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
        , object_name
        , operational_status
        , orbit_class
        , owner_country
        , launch_year
        , mission_category_labels
        , ownership_class_labels
        , launch_vehicle_brand
        , site_location_country
    from {{ ref('fct__satellite_master') }}
)

, cte_tracked_objects as (
    select
        gp.satcat_id
        , gp.object_id
        -- the enrichment mart's name when the object is enriched, else Space-Track's
        , coalesce(sat.object_name, gp.object_name) as object_name
        , gp.object_type
        , gp.epoch
        , gp.mean_motion
        , gp.eccentricity
        , gp.inclination
        , gp.ra_of_asc_node
        , gp.arg_of_pericenter
        , gp.mean_anomaly
        , gp.bstar
        , gp.mean_motion_dot
        , gp.mean_motion_ddot
        , gp.rev_at_epoch
        , gp.element_set_no
        , gp.ephemeris_type
        , gp.classification_type
        , gp.orbital_period
        , sat.operational_status
        , sat.orbit_class
        , sat.owner_country
        , sat.launch_year
        , sat.mission_category_labels
        , sat.ownership_class_labels
        , sat.launch_vehicle_brand
        , sat.site_location_country
    from cte_fct__gp_elements as gp
    left join cte_fct__satellite_master as sat
        on gp.satcat_id = sat.satcat_id
    -- a full element set: every field a propagator needs
    where gp.epoch is not null
        and gp.mean_motion is not null
        and gp.eccentricity is not null
        and gp.inclination is not null
        and gp.ra_of_asc_node is not null
        and gp.arg_of_pericenter is not null
        and gp.mean_anomaly is not null
        and gp.bstar is not null
        and gp.mean_motion_dot is not null
        and gp.mean_motion_ddot is not null
        and gp.rev_at_epoch is not null
        and gp.element_set_no is not null
        and gp.ephemeris_type is not null
        and gp.classification_type is not null
        and gp.orbital_period > 0
)

, cte_final as (
    select
        cast(satcat_id as bigint) as satcat_id
        , cast(object_id as varchar) as object_id
        , cast(object_name as varchar) as object_name
        , cast(object_type as varchar) as object_type
        , strftime(epoch, '%Y-%m-%dT%H:%M:%S.%f') as epoch
        , cast(mean_motion as double) as mean_motion
        , cast(eccentricity as double) as eccentricity
        , cast(inclination as double) as inclination
        , cast(ra_of_asc_node as double) as ra_of_asc_node
        , cast(arg_of_pericenter as double) as arg_of_pericenter
        , cast(mean_anomaly as double) as mean_anomaly
        , cast(bstar as double) as bstar
        , cast(mean_motion_dot as double) as mean_motion_dot
        , cast(mean_motion_ddot as double) as mean_motion_ddot
        , cast(rev_at_epoch as bigint) as rev_at_epoch
        , cast(element_set_no as bigint) as element_set_no
        , cast(ephemeris_type as bigint) as ephemeris_type
        , cast(classification_type as varchar) as classification_type
        , cast(orbital_period as double) as orbital_period
        , cast(operational_status as varchar) as operational_status
        , cast(orbit_class as varchar) as orbit_class
        , cast(owner_country as varchar) as owner_country
        , cast(launch_year as bigint) as launch_year
        , cast(coalesce(mission_category_labels, []) as varchar[]) as mission_category_labels
        , cast(coalesce(ownership_class_labels, []) as varchar[]) as ownership_class_labels
        , cast(launch_vehicle_brand as varchar) as launch_vehicle_brand
        , cast(site_location_country as varchar) as site_location_country
    from cte_tracked_objects
)

select * from cte_final
order by satcat_id

-- One row per object in a constellation or a satellite system (D-047), with the names the master shows: its
-- constellation, its primary system, and every system it belongs to as a list: the primary system first, then the
-- others in name order.
-- One model feeds all three so fct__satellite_master reads one relation for them.
with cte_int__xsrc__satellite_constellation as (
    select
        satcat_id
        , satellite_constellation_name
    from {{ ref('int__xsrc__satellite_constellation') }}
)

, cte_int__xsrc__satellite_system_membership as (
    select
        satcat_id
        , satellite_system_name
        , flag_primary_system
    from {{ ref('int__xsrc__satellite_system_membership') }}
)

, cte_system_lists as ( -- per object: the primary system and the ordered list of all its systems
    select
        satcat_id
        , max(case when flag_primary_system = 1 then satellite_system_name end) as primary_satellite_system_name
        , list(satellite_system_name order by flag_primary_system desc, satellite_system_name) as satellite_system_names
    from cte_int__xsrc__satellite_system_membership
    group by
        satcat_id
)

, cte_group_names as ( -- an object may have a constellation, systems, or both
    select
        coalesce(con.satcat_id, sys.satcat_id) as satcat_id
        , con.satellite_constellation_name
        , sys.primary_satellite_system_name
        , coalesce(sys.satellite_system_names, cast([] as varchar[])) as satellite_system_names
    from cte_int__xsrc__satellite_constellation as con
    full outer join cte_system_lists as sys
        on sys.satcat_id = con.satcat_id
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(satellite_constellation_name as varchar) as satellite_constellation_name
        , cast(primary_satellite_system_name as varchar) as primary_satellite_system_name
        , cast(satellite_system_names as varchar[]) as satellite_system_names
        , {{ helper__audit_fields() }}
    from cte_group_names
)

select * from cte_final

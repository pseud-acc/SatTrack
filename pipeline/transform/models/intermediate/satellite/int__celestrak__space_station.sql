-- One row per object in a configured CelesTrak space station group (D-043): today `stations`, CelesTrak's "Space
-- Stations" (the ISS and Tiangong modules and the spacecraft visiting them). Feeds fct__satellite_master's
-- flag_space_station (1 here; the mart defaults objects not listed to 0). Station groups never set the
-- constellation (int__celestrak__satellite_constellation).
with cte_stg__celestrak__gp_group_member as (
    select
        celestrak_group
        , satcat_id
    from {{ ref('stg__celestrak__gp_group_member') }}
)

, cte_stg__celestrak__group_config as (
    select
        celestrak_group
        , celestrak_group_kind
    from {{ ref('stg__celestrak__group_config') }}
)

, cte_station_members as ( -- objects in any group the config marks as a station group
    select distinct
        mem.satcat_id
    from cte_stg__celestrak__gp_group_member as mem
    inner join cte_stg__celestrak__group_config as cfg
        on cfg.celestrak_group = mem.celestrak_group
    where cfg.celestrak_group_kind = 'station'
        and mem.satcat_id is not null
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(1 as integer) as flag_space_station
        , {{ helper__audit_fields() }}
    from cte_station_members
)

select * from cte_final

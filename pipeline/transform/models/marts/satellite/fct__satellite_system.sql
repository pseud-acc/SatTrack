-- One row per satellite per satellite system it belongs to (D-047): its primary system (flag_primary_system = 1) and
-- any system it hosts a payload for (0), e.g. a Galileo satellite carrying a Cospas-Sarsat repeater.
with cte_int__xsrc__satellite_system_membership as (
    select
        satcat_id
        , satellite_system_name
        , flag_primary_system
        , system_source
    from {{ ref('int__xsrc__satellite_system_membership') }}
)

, cte_final as (
    select
        cast(satcat_id as integer) as satcat_id
        , cast(satellite_system_name as varchar) as satellite_system_name
        , cast(flag_primary_system as integer) as flag_primary_system
        , cast(system_source as varchar) as system_source
        , {{ helper__audit_fields() }}
    from cte_int__xsrc__satellite_system_membership
)

select * from cte_final

-- One row per satellite per owner country (every country in the owner_country_codes list of fct__satellite_master).
with cte_int__xsrc__satellite_owner_country_map as (
    select
        map_id
        , satcat_id
        , country_key
        , owner_country_iso_code
        , owner_country_iso_code_ord
        , owner_country_source
    from {{ ref('int__xsrc__satellite_owner_country_map') }}
)

, cte_final as (
    select
        cast(map_id as varchar) as map_id
        , cast(satcat_id as integer) as satcat_id
        , cast(country_key as varchar) as country_key
        , cast(owner_country_iso_code as varchar) as owner_country_iso_code
        , cast(owner_country_iso_code_ord as integer) as owner_country_iso_code_ord
        , cast(owner_country_source as varchar) as owner_country_source
        , {{ helper__audit_fields() }}
    from cte_int__xsrc__satellite_owner_country_map
)

select * from cte_final

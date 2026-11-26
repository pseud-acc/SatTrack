-- One row per satellite system SatTrack shows (D-047), with where it comes from (CelesTrak, or the ad-hoc seed of
-- manual ones with their publisher's details) and how many objects in the GP feed it names.
with cte_int__xsrc__satellite_system_definition as (
    select
        satellite_system_name
        , system_origin
        , definition_rule_type
        , definition_rule_values
        , definition_operator
        , definition_purpose
        , definition_description
        , definition_source_name
        , definition_source_url
        , definition_source_quote
        , satellite_count
        , primary_satellite_count
    from {{ ref('int__xsrc__satellite_system_definition') }}
)

, cte_final as (
    select
        cast(satellite_system_name as varchar) as satellite_system_name
        , cast(system_origin as varchar) as system_origin
        , cast(definition_rule_type as varchar) as definition_rule_type
        , cast(definition_rule_values as varchar) as definition_rule_values
        , cast(definition_operator as varchar) as definition_operator
        , cast(definition_purpose as varchar) as definition_purpose
        , cast(definition_description as varchar) as definition_description
        , cast(definition_source_name as varchar) as definition_source_name
        , cast(definition_source_url as varchar) as definition_source_url
        , cast(definition_source_quote as varchar) as definition_source_quote
        , cast(satellite_count as integer) as satellite_count
        , cast(primary_satellite_count as integer) as primary_satellite_count
        , {{ helper__audit_fields() }}
    from cte_int__xsrc__satellite_system_definition
)

select * from cte_final

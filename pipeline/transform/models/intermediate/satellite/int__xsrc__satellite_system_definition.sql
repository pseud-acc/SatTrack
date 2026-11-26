-- One row per system SatTrack shows (D-047): every name int__xsrc__satellite_system_membership gives an object, plus any
-- system in the ad-hoc seed manual_satellite_grouping that matches no object (kept, count 0, and warned about).
-- Names from CelesTrak carry no details (CelesTrak publishes the group title only); seed rows carry their
-- publisher's operator, purpose, description, URL and quote.
with cte_int__xsrc__satellite_system_membership as (
    select
        satcat_id
        , satellite_system_name
        , flag_primary_system
    from {{ ref('int__xsrc__satellite_system_membership') }}
)

, cte_stg__sattrack__manual_satellite_grouping as (
    select
        grouping_kind
        , grouping_name
        , definition_rule_type
        , definition_rule_values
        , definition_operator
        , definition_purpose
        , definition_description
        , definition_source_name
        , definition_source_url
        , definition_source_quote
    from {{ ref('stg__sattrack__manual_satellite_grouping') }}
)

, cte_manual_systems as (
    select
        grouping_name as satellite_system_name
        , definition_rule_type
        , definition_rule_values
        , definition_operator
        , definition_purpose
        , definition_description
        , definition_source_name
        , definition_source_url
        , definition_source_quote
    from cte_stg__sattrack__manual_satellite_grouping
    where grouping_kind = 'system'
)

, cte_member_counts as ( -- per name: how many objects it names
    select
        satellite_system_name
        , count(*) as satellite_count
        , sum(flag_primary_system) as primary_satellite_count
    from cte_int__xsrc__satellite_system_membership
    group by
        satellite_system_name
)

, cte_definitions as ( -- every named system, with seed details where it has them
    select
        coalesce(cnt.satellite_system_name, man.satellite_system_name) as satellite_system_name
        , case when man.satellite_system_name is not null then 'manual' else 'celestrak' end as system_origin
        , man.definition_rule_type
        , man.definition_rule_values
        , man.definition_operator
        , man.definition_purpose
        , man.definition_description
        , man.definition_source_name
        , man.definition_source_url
        , man.definition_source_quote
        , coalesce(cnt.satellite_count, 0) as satellite_count
        , coalesce(cnt.primary_satellite_count, 0) as primary_satellite_count
    from cte_member_counts as cnt
    full outer join cte_manual_systems as man
        on man.satellite_system_name = cnt.satellite_system_name
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
    from cte_definitions
)

select * from cte_final

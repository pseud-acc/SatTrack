-- 1:1 with the ad-hoc seed manual_satellite_grouping (D-047): cast and clean only (the seed uses the project's names).
-- A seed is read with ref(), so it gets its import CTE (SQL-01) ahead of cte_final.
with cte_manual_satellite_grouping as (
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
        , flag_hosted_system
    from {{ ref('manual_satellite_grouping') }}
)

, cte_final as (
    select
        cast(grouping_kind as varchar) as grouping_kind
        , cast(grouping_name as varchar) as grouping_name
        , cast(definition_rule_type as varchar) as definition_rule_type
        , cast(definition_rule_values as varchar) as definition_rule_values
        , cast(nullif(trim(definition_operator), '') as varchar) as definition_operator
        , cast(nullif(trim(definition_purpose), '') as varchar) as definition_purpose
        , cast(definition_description as varchar) as definition_description
        , cast(definition_source_name as varchar) as definition_source_name
        , cast(definition_source_url as varchar) as definition_source_url
        , cast(definition_source_quote as varchar) as definition_source_quote
        , cast(flag_hosted_system as integer) as flag_hosted_system
    from cte_manual_satellite_grouping
)

select * from cte_final

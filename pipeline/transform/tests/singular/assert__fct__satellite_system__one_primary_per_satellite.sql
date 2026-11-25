-- Fails (D-047): a satellite with more than one primary system. Each GCAT programme family maps to one system, so two
-- primaries mean two systems claim the same family (e.g. a manual row repeating a CelesTrak system's family).
with cte_fct__satellite_system as (
    select
        satcat_id
        , satellite_system_name
        , flag_primary_system
    from {{ ref('fct__satellite_system') }}
)

select
    satcat_id
    , count(*) as primary_systems
    , string_agg(satellite_system_name, ', ' order by satellite_system_name) as satellite_system_names
from cte_fct__satellite_system
where flag_primary_system = 1
group by
    satcat_id
having count(*) > 1

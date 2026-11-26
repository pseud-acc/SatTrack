-- Fails (D-047): an object whose system list doesn't start with its primary system, lists a system twice, or has
-- systems but no list. Checked on the built table because dbt unit tests can't compare list columns.
with cte_int__xsrc__satellite_group_names as (
    select
        satcat_id
        , primary_satellite_system_name
        , satellite_system_names
    from {{ ref('int__xsrc__satellite_group_names') }}
)

select
    satcat_id
    , primary_satellite_system_name
    , satellite_system_names
from cte_int__xsrc__satellite_group_names
where satellite_system_names is null
    or (primary_satellite_system_name is not null and satellite_system_names[1] <> primary_satellite_system_name)
    or len(satellite_system_names) <> len(list_distinct(satellite_system_names))

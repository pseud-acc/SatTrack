-- Overview tab: one-row headline figures for the app mart.
with cte_fct__satellite_master as (
    select
        satcat_id
        , object_type
        , status
        , flag_gcat_matched
        , satellite_program
        , positions_as_of
        , details_as_of
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        count(*) as objects
        , count(*) filter (where object_type = 'PAYLOAD') as payloads
        , count(*) filter (where status = 'Active') as active_objects
        , avg(cast(flag_gcat_matched as integer)) as gcat_match_rate
        , count(distinct satellite_program) as programs
        , strftime(max(positions_as_of), '%Y-%m-%d %H:%M UTC') as positions_as_of
        , strftime(max(details_as_of), '%Y-%m-%d %H:%M UTC') as details_as_of
    from cte_fct__satellite_master
)

select * from cte_final

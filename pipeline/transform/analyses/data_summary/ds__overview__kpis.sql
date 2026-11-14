-- Overview tab: one-row headline figures for the app mart.
with cte_fct__satellite_master as (
    select
        satcat_id
        , object_type
        , operational_status
        , flag_gcat_matched
        , satellite_program
        , positions_as_of
        , gcat_updated_at
    from {{ ref('fct__satellite_master') }}
)

, cte_final as (
    select
        count(*) as objects
        , count(*) filter (where object_type = 'PAYLOAD') as payloads
        , count(*) filter (where operational_status = 'Active') as active_objects
        , avg(flag_gcat_matched) as gcat_match_rate
        , count(distinct satellite_program) as programs
        , strftime(max(positions_as_of), '%Y-%m-%d %H:%M UTC') as positions_as_of
        , strftime(max(gcat_updated_at), '%Y-%m-%d %H:%M UTC') as gcat_updated_at
    from cte_fct__satellite_master
)

select * from cte_final

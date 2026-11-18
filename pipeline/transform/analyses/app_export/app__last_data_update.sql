-- App export: last_data_update.csv, the data-freshness file the SatTrack Dash app loads. The app reads the
-- 'Last Update' of the row whose Source is 'SpaceTrack_GP' and shows it in the page header as "Last updated: <value>".
-- Timestamps use the old file's format, dd/mm/YYYY, HH:MM:SS (UTC here).
--   SpaceTrack_GP  when the element sets (Space-Track GP) were downloaded: from the tracking unit, the same table
--                  the app's TLE lines come from (app__satcat_tle), so it moves on even when enrichment is held
--   GCAT           GCAT's own last-updated time for the catalogue; its download time is not kept in the marts
with cte_fct__gp_elements as (
    select
        _loaded_at
    from {{ ref('fct__gp_elements') }}
)

, cte_fct__satellite_master as (
    select
        gcat_updated_at
    from {{ ref('fct__satellite_master') }}
)

, cte_positions_as_of as (
    select
        max(_loaded_at) as positions_as_of
    from cte_fct__gp_elements
)

, cte_gcat_as_of as (
    select
        max(gcat_updated_at) as gcat_updated_at
    from cte_fct__satellite_master
)

, cte_as_of as (
    select
        pos.positions_as_of
        , gcat.gcat_updated_at
    from cte_positions_as_of as pos
    cross join cte_gcat_as_of as gcat
)

, cte_sources as (
    select
        'SpaceTrack_GP' as source
        , positions_as_of as last_download
        , positions_as_of as last_update
    from cte_as_of

    union all

    select
        'GCAT' as source
        , cast(null as timestamp) as last_download
        , gcat_updated_at as last_update
    from cte_as_of
)

, cte_final as (
    select
        cast(source as varchar) as "Source"
        , strftime(last_download, '%d/%m/%Y, %H:%M:%S') as "Last Download"
        , strftime(last_update, '%d/%m/%Y, %H:%M:%S') as "Last Update"
    from cte_sources
)

select * from cte_final
order by "Source"

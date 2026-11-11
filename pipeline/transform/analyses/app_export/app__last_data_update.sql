-- App export: last_data_update.csv, the data-freshness file the live SatTrack Dash app loads (repo path
-- dat/meta/last_data_update.csv). The app reads only the 'Last Update' of the row whose Source is 'Celestrak_TLE'
-- and shows it in the page header as "Last updated: <value>", so that row keeps its old name.
-- Timestamps use the old file's format, dd/mm/YYYY, HH:MM:SS (UTC here).
--   Celestrak_TLE  compatibility row for the app: when the element sets (now Space-Track GP) were downloaded
--   SpaceTrack_GP  the same time under the publisher's own name
--   GCAT           GCAT's own last-updated time for the catalogue; its download time is not kept in the marts
with cte_fct__satellite_master as (
    select
        positions_as_of
        , gcat_updated_at
    from {{ ref('fct__satellite_master') }}
)

, cte_as_of as (
    select
        max(positions_as_of) as positions_as_of
        , max(gcat_updated_at) as gcat_updated_at
    from cte_fct__satellite_master
)

, cte_sources as (
    select
        'Celestrak_TLE' as source
        , positions_as_of as last_download
        , positions_as_of as last_update
    from cte_as_of

    union all

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

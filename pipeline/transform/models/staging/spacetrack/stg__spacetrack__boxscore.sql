-- 1:1 with raw_spacetrack.boxscore: rename + cast only.
with cte_final as (
    select
        cast("SPADOC_CD" as varchar) as country_code
        , cast("COUNTRY" as varchar) as spacetrack_country_name
        , try_cast("ORBITAL_PAYLOAD_COUNT" as integer) as boxscore_orbital_payload_count
        , try_cast("ORBITAL_TOTAL_COUNT" as integer) as boxscore_orbital_total_count
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
    from {{ source('spacetrack', 'boxscore') }}
)

select * from cte_final

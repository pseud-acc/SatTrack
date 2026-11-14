-- 1:1 with raw_jsr.gcat_code_labels (GCAT code tables parsed from pcols.html at ingestion): rename + cast only.
with cte_final as (
    select
        cast("domain" as varchar) as label_domain
        , cast(gcat_code as varchar) as gcat_code
        , cast(gcat_meaning as varchar) as gcat_meaning
        , cast(short_label as varchar) as short_label
        , cast(_source_url as varchar) as _source_url
        , cast(_loaded_at as timestamp) as _loaded_at
        , _run_id
    from {{ source('jsr', 'gcat_code_labels') }}
)

select * from cte_final

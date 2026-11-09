-- One row per GCAT Org Code (organisation phase), with the display name rule:
-- English short name, else the host-language short name (GCAT: ShortEName "can be omitted when
-- ShortName is itself English"). Undocumented class values become NULL.
with cte_stg__jsr__orgs as (
    select
        org_code
        , org_ucode
        , org_state_code
        , org_type
        , org_class
        , org_short_name
        , org_full_name
        , org_short_name_en
        , org_full_name_en
        , org_location
        , org_latitude
        , org_longitude
        , org_parent_code
        , org_start_date_raw
        , org_stop_date_raw
        , _source_updated_at
    from {{ ref('stg__jsr__orgs') }}
)

, cte_final as (
    select
        org_code
        , org_ucode
        , org_state_code
        , org_type
        , case when org_class in ('A', 'B', 'C', 'D') then org_class end as org_class
        , coalesce(org_short_name_en, org_short_name) as org_display_name
        , coalesce(org_full_name_en, org_full_name) as org_display_full_name
        , org_short_name
        , org_full_name
        , org_short_name_en
        , org_full_name_en
        , org_location
        , org_latitude
        , org_longitude
        , org_parent_code
        , {{ helper__parse_vague_date_columns('org_start_date_raw', 'org_start_date') }}
        , {{ helper__parse_vague_date_columns('org_stop_date_raw', 'org_stop_date') }}
        -- GCAT: a null stop date means "still in operation, or assumed to be so"
        , (org_stop_date_raw is null or org_stop_date_raw = '*') as flag_org_active
        -- GCAT: only CY, IGO and AP types are reliable; they mark country-like organisations
        , list_has_any(string_split(coalesce(org_type, ''), '/'), ['CY', 'IGO', 'AP']) as flag_country_like
        , _source_updated_at
        , {{ helper__audit_fields() }}
    from cte_stg__jsr__orgs
)

select * from cte_final

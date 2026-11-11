-- One row per GCAT object (satcat + satcat100k): for rocket stages, components and debris (Type R / C / D), the first
-- payload reached by following GCAT Parent links. GCAT cols.html: Parent is "the 'parent object' which the object is
-- attached to at the start of the phase" - an Extended JCAT ID ("usually just a JCAT ID", sometimes with a port suffix
-- or a trailing '*') - or a central body name. Only catalogued objects are walked; payloads never inherit.
with recursive cte_parent_walk_limits as ( -- guard against cycles and runaway chains (observed chains are <= 5 steps)
    select
        10 as max_parent_depth
)

, cte_int__jsr__satellite_catalogue as (
    select
        jcat
        , sat_type_class
        , parent_ref
    from {{ ref('int__jsr__satellite_catalogue') }}
)

, cte_parent_links as ( -- the Extended JCAT ID's leading JCAT ID (one prefix letter + sequence number); body names give NULL
    select
        jcat
        , sat_type_class
        , parent_ref
        , nullif(regexp_extract(parent_ref, '^[A-Z][0-9]+'), '') as parent_jcat
    from cte_int__jsr__satellite_catalogue
)

, cte_parent_walk as ( -- one row per step up the chain; a walk stops at the first payload, a missing object, a repeat or the limit
    select
        jcat as start_jcat
        , parent_jcat as step_jcat
        , 1 as step_depth
        , [jcat] as visited_jcats
    from cte_parent_links
    where sat_type_class in ('R', 'C', 'D')
      and parent_jcat is not null
    union all
    select
        walk.start_jcat
        , link.parent_jcat as step_jcat
        , walk.step_depth + 1 as step_depth
        , list_append(walk.visited_jcats, walk.step_jcat) as visited_jcats
    from cte_parent_walk as walk
    join cte_parent_links as link on link.jcat = walk.step_jcat
    cross join cte_parent_walk_limits as limits
    where coalesce(link.sat_type_class, '') <> 'P'
      and link.parent_jcat is not null
      and walk.step_depth < limits.max_parent_depth
      and not list_contains(list_append(walk.visited_jcats, walk.step_jcat), link.parent_jcat)
)

, cte_walk_ends as ( -- the last step of each walk, with what was found there
    select
        walk.start_jcat
        , walk.step_jcat
        , walk.step_depth
        , link.jcat is not null as step_in_catalogue
        , coalesce(link.sat_type_class = 'P', false) as step_is_payload
        , link.parent_jcat is not null as step_has_parent
    from cte_parent_walk as walk
    left join cte_parent_links as link on link.jcat = walk.step_jcat
    qualify row_number() over (partition by walk.start_jcat order by walk.step_depth desc) = 1
)

, cte_final as (
    select
        link.jcat
        , link.sat_type_class
        , link.parent_ref
        , link.parent_jcat
        , case when ends.step_is_payload then ends.step_jcat end as parent_payload_jcat
        , case when ends.step_is_payload then ends.step_depth end as parent_payload_depth
        , case
            when link.sat_type_class = 'P' then 'payload_object'
            when link.sat_type_class is null then 'type_unclassified'
            when link.parent_jcat is null then 'no_parent_object'
            when ends.step_is_payload then 'payload_found'
            when not ends.step_in_catalogue then 'parent_not_in_catalogue'
            when not ends.step_has_parent then 'chain_ends_without_payload'
            else 'chain_limit'
        end as parent_payload_search_outcome
        , {{ helper__audit_fields() }}
    from cte_parent_links as link
    left join cte_walk_ends as ends on ends.start_jcat = link.jcat
)

select * from cte_final

{#- model_health: the hub for basic model checks (plan section 16.2).
    Each check is a SEPARATE named invocation in yml (mh__<model>__<check>) so it stays discoverable,
    selectable and tracked on its own; this macro holds the logic and the categorisation.
    Failing rows always carry check_name, so stored failures say which check broke.
    Severity comes from dbt_project.yml by path (staging warn, intermediate/marts error).

    Checks:
      pk_unique        - columns: list; no duplicate key values
      pk_not_null      - columns: list; no NULL in any key column
      row_count_match  - source-vs-target reconciliation (NOT an anomaly test; volume drift is
                         Elementary's job). compare_to: ref()/source() the model is built from;
                         relationship: equal (1:1 models) | lte (dedup / filter) | gte (union / fan-out);
                         optional min_ratio: lower bound on target/compare_to for lossy steps. -#}
{% test model_health(model, check, columns=none, compare_to=none, relationship='equal', min_ratio=none) %}
{{ config(meta={'category': 'critical', 'check': check, 'hub': 'model_health'}) }}

{%- if check == 'pk_unique' %}
select
    'pk_unique' as check_name
    , {{ columns | join('\n    , ') }}
    , count(*) as n_rows
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1

{%- elif check == 'pk_not_null' %}
select
    'pk_not_null' as check_name
    , {{ columns | join('\n    , ') }}
from {{ model }}
where {% for c in columns %}{{ c }} is null{% if not loop.last %} or {% endif %}{% endfor %}

{%- elif check == 'row_count_match' %}
{%- if compare_to is none %}{{ exceptions.raise_compiler_error("model_health row_count_match needs compare_to") }}{% endif %}
{%- set ops = {'equal': '=', 'lte': '<=', 'gte': '>='} %}
{%- if relationship not in ops %}{{ exceptions.raise_compiler_error("model_health row_count_match: relationship must be equal, lte or gte") }}{% endif %}
with cte_target as (
    select
        count(*) as target_rows
    from {{ model }}
)
, cte_source as (
    select
        count(*) as source_rows
    from {{ compare_to }}
)
select
    'row_count_match' as check_name
    , '{{ relationship }}' as relationship
    , t.target_rows
    , s.source_rows
    , {% if min_ratio is not none %}{{ min_ratio }}{% else %}null{% endif %} as min_ratio
from cte_target as t
cross join cte_source as s
where not (t.target_rows {{ ops[relationship] }} s.source_rows)
   {%- if min_ratio is not none %}
   or t.target_rows < s.source_rows * {{ min_ratio }}
   {%- endif %}

{%- else %}
{{ exceptions.raise_compiler_error("model_health: unknown check '" ~ check ~ "' (expected pk_unique, pk_not_null, row_count_match)") }}
{%- endif %}
{% endtest %}

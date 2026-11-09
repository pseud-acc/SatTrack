{#- lv_brand: deterministic launch-vehicle brand from GCAT's own vehicle name (decided 2026-10-25).
    1. drop the upper stage after '/';  2. strip trailing variant tokens (digits, Roman numerals,
    XL/DL/QL, Block, Heavy, Mk, short config codes);  3. a 1-2 char stem keeps the next token's Roman
    core (H-IIA -> H-II);  4. a letters-only stub of <= 3 chars reverts to the full first segment
    (SS-520, KT-2). Ported from the Python prototype; parity-tested on all GCAT LV names. -#}
{% macro helper__derive_lv_brand(col) -%}
{%- set var_re = "^(\\d[\\w.+(),]*|[IVX]+[A-Z]*\\+?|[vV]\\d[\\w.]*|Block|Heavy|Light|Lite|XL|DL|QL|Mk|[A-Z]{1,3}\\d*[A-Z]?\\+?|\\d+[A-Za-z]+\\+?[\\w(),]*|\\([^)]*\\))$" -%}
(with cte_first_segment as ( -- 1. drop the upper stage after '/'
    select
        trim(split_part({{ col }}, '/', 1)) as s
)
, cte_words as (
    select
        s
        , list_filter(regexp_split_to_array(s, '[ -]'), lambda t: t <> '') as words
    from cte_first_segment
)
, cte_kept_words as ( -- 2. keep up to the last word that is not a variant token
    select
        s
        , words
        , coalesce(list_max(list_transform(
            list_filter(list_zip(words, generate_series(1, len(words))), lambda z: not regexp_matches(z[1], '{{ var_re }}')),
            lambda z: z[2])), 1) as keep_n
    from cte_words
)
, cte_stem as (
    select
        s
        , words
        , keep_n
        , regexp_extract(s, '^((?:[^ -]+[ -]+){' || (keep_n - 1) || '}[^ -]+)', 1) as out
    from cte_kept_words
)
, cte_roman_core as ( -- 3. a 1-2 char stem keeps the next token's Roman core
    select
        s
        , case
            when length(out) <= 2 and keep_n < len(words) and regexp_matches(words[keep_n + 1], '^[IVX]+[A-Z]*\+?$')
                then out || substr(s, length(out) + 1, 1) || regexp_extract(words[keep_n + 1], '^([IVX]+)', 1)
            else out
        end as out
    from cte_stem
)
select -- 4. a letters-only stub of <= 3 chars reverts to the full first segment
    case when length(out) <= 3 and regexp_full_match(out, '[A-Za-z]+') and out <> s then s else out end
from cte_roman_core)
{%- endmacro %}

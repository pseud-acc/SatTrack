-- Fails when the vague-date macros disagree with the example table on GCAT's Vague Date page
-- (https://planet4589.org/space/gcat/web/intro/vague.html). For each value: the date as written (base: the flags
-- are ignored), the range start and end it implies (a trailing '?' widens the range by one unit of the precision on
-- each side) and its precision. The millisecond row is not parsed (GCAT Launch_Date has one-second precision).
with cte_gcat_examples as (
    select
        vague_date
        , expected_base
        , expected_start
        , expected_end
        , expected_precision
    from (values
        ('2016 Jun 8 2355:57', timestamp '2016-06-08 23:55:57', timestamp '2016-06-08 23:55:57', timestamp '2016-06-08 23:55:58', 'second')
        , ('2016 Jun 8 2355:57?', timestamp '2016-06-08 23:55:57', timestamp '2016-06-08 23:55:56', timestamp '2016-06-08 23:55:59', 'second?')
        , ('2016 Jun 8 2355', timestamp '2016-06-08 23:55:00', timestamp '2016-06-08 23:55:00', timestamp '2016-06-08 23:56:00', 'minute')
        , ('2016 Jun 8 2355?', timestamp '2016-06-08 23:55:00', timestamp '2016-06-08 23:54:00', timestamp '2016-06-08 23:57:00', 'minute?')
        , ('2016 Jun 8.98', timestamp '2016-06-08 23:31:12', timestamp '2016-06-08 23:31:12', timestamp '2016-06-08 23:45:36', 'centiday')
        , ('2016 Jun 8.98?', timestamp '2016-06-08 23:31:12', timestamp '2016-06-08 23:16:48', timestamp '2016-06-09 00:00:00', 'centiday?')
        , ('2016 Jun 8 23h', timestamp '2016-06-08 23:00:00', timestamp '2016-06-08 23:00:00', timestamp '2016-06-09 00:00:00', 'hour')
        , ('2016 Jun 8.9', timestamp '2016-06-08 21:36:00', timestamp '2016-06-08 21:36:00', timestamp '2016-06-09 00:00:00', 'centiday')
        , ('2016 Jun 8', timestamp '2016-06-08 00:00:00', timestamp '2016-06-08 00:00:00', timestamp '2016-06-09 00:00:00', 'day')
        , ('2016 Jun 8s', timestamp '2016-06-08 00:00:00', timestamp '2016-06-08 00:00:00', timestamp '2016-06-09 00:00:00', 'day')
        , ('2016 Jun 8?', timestamp '2016-06-08 00:00:00', timestamp '2016-06-07 00:00:00', timestamp '2016-06-10 00:00:00', 'day?')
        , ('2016 Jun', timestamp '2016-06-01 00:00:00', timestamp '2016-06-01 00:00:00', timestamp '2016-07-01 00:00:00', 'month')
        , ('2016 Jun?', timestamp '2016-06-01 00:00:00', timestamp '2016-05-01 00:00:00', timestamp '2016-08-01 00:00:00', 'month?')
        , ('2016 Q2', timestamp '2016-04-01 00:00:00', timestamp '2016-04-01 00:00:00', timestamp '2016-07-01 00:00:00', 'quarter')
        , ('2016 Q2?', timestamp '2016-04-01 00:00:00', timestamp '2016-01-01 00:00:00', timestamp '2016-10-01 00:00:00', 'quarter?')
        , ('2016', timestamp '2016-01-01 00:00:00', timestamp '2016-01-01 00:00:00', timestamp '2017-01-01 00:00:00', 'year')
        , ('2016?', timestamp '2016-01-01 00:00:00', timestamp '2015-01-01 00:00:00', timestamp '2018-01-01 00:00:00', 'year?')
        , ('2010s', timestamp '2010-01-01 00:00:00', timestamp '2010-01-01 00:00:00', timestamp '2020-01-01 00:00:00', 'decade')
        , ('2010s?', timestamp '2010-01-01 00:00:00', timestamp '2000-01-01 00:00:00', timestamp '2030-01-01 00:00:00', 'decade?')
        , ('21C', timestamp '2001-01-01 00:00:00', timestamp '2001-01-01 00:00:00', timestamp '2101-01-01 00:00:00', 'century')
        , ('21C?', timestamp '2001-01-01 00:00:00', timestamp '1901-01-01 00:00:00', timestamp '2201-01-01 00:00:00', 'century?')
        , ('3M', timestamp '2001-01-01 00:00:00', timestamp '2001-01-01 00:00:00', timestamp '3001-01-01 00:00:00', 'millennium')
        , ('3M?', timestamp '2001-01-01 00:00:00', timestamp '1001-01-01 00:00:00', timestamp '4001-01-01 00:00:00', 'millennium?')
        -- not in the example table: three-digit years as GCAT orgs write them (TStart of ENG and DK)
        , ('927 Jul 12', timestamp '0927-07-12 00:00:00', timestamp '0927-07-12 00:00:00', timestamp '0927-07-13 00:00:00', 'day')
        , ('700?', timestamp '0700-01-01 00:00:00', timestamp '0699-01-01 00:00:00', timestamp '0702-01-01 00:00:00', 'year?')
    ) as t(vague_date, expected_base, expected_start, expected_end, expected_precision)
)

, cte_parsed as (
    select
        vague_date
        , expected_base
        , expected_start
        , expected_end
        , expected_precision
        , {{ helper__parse_vague_date_columns('vague_date', 'parsed') }}
    from cte_gcat_examples
)

select
    vague_date
    , expected_base
    , parsed
    , expected_start
    , parsed_start
    , expected_end
    , parsed_end
    , expected_precision
    , parsed_precision
from cte_parsed
where parsed is distinct from expected_base
   or parsed_start is distinct from expected_start
   or parsed_end is distinct from expected_end
   or parsed_precision is distinct from expected_precision

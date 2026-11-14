{% docs src__spacetrack %}
Space-Track.org, the USSPACECOM outlet for unclassified space domain awareness data. SatTrack uses the **GP class**: "an efficient listing of the newest SGP4 keplerian element set for each man-made earth-orbiting object tracked by the 18th Space Defense Squadron" ([Space-Track documentation](https://www.space-track.org/documentation)), and the **boxscore** class for country-code meanings.
{% enddocs %}

{% docs tbl__spacetrack__gp %}
Newest GP element set per on-orbit object (query `decay_date/null-val/epoch/>now-10`), in CCSDS OMM keywords ([CCSDS 502.0-B-3](https://public.ccsds.org/Pubs/502x0b3e1.pdf)). One row per `NORAD_CAT_ID`.
{% enddocs %}

{% docs src__jsr %}
GCAT, the General Catalog of Artificial Space Objects by Jonathan C. McDowell ([planet4589.org/space/gcat](https://planet4589.org/space/gcat/)). Public TSV files; each carries its data update time in a `# Updated` row.
{% enddocs %}

{% docs tbl__jsr__satcat %}
GCAT object catalog. Column meanings: [Object Catalog Column Descriptions](https://planet4589.org/space/gcat/web/cat/cols.html).
{% enddocs %}

{% docs tbl__jsr__psatcat %}
GCAT payload catalog. Column meanings: [Payload Catalog Column Descriptions](https://planet4589.org/space/gcat/web/cat/pcols.html).
{% enddocs %}


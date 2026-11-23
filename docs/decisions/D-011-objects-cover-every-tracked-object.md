# D-011 Objects file covers every tracked object; UNKNOWN hidden by default

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #57 (decision), #58 (plan 2.1)
**Component:** the `objects` dataset · **Tier:** full

## Context
Today's app shows payloads only. The browser viewer can show every tracked object, and several planned features
need rocket bodies and debris.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Every object in the GP feed, with `object_type`; UNKNOWN hidden in the UI** | Re-entries, conjunctions, statistics, replay and bright passes all need rocket bodies and debris; the UNKNOWN rule comes from source data | +0.72 MB against payloads only (1.70 vs 0.98 MB Brotli) | All Phase 3–7 object features |
| Payloads only | Smallest | A second dataset later for every other type | Blocks re-entries and conjunctions |
| Every object, UNKNOWN excluded | Slightly smaller | Drops real tracked objects | – |

## Decision
Include every object in the GP feed (32,652 on 21 Nov: 19,742 payloads, 10,179 debris, 2,219 rocket bodies, 512
UNKNOWN). The 512 UNKNOWN objects are Space-Track analyst objects named "TBA - TO BE ASSIGNED", with no international
designator, GCAT match, launch year or owner: included, and hidden in the UI unless switched on. Display defaults for
debris and rocket bodies were left to the Cesium spike.

## Evidence
Sizes above, from the 21 Nov export.

## Consequences
- The filter spec needs a rule for missing values: decided in 2.2 (explicit; no clause matches a missing value unless
  it says so).
- The Cesium decisions set the display default: payloads only, with toggles for rocket bodies and debris.

## Revisit when
- The catalogue passes ~45k objects: re-run the Cesium performance matrix.

## Related
D-009, D-010; the Cesium decisions (default object set); filter spec decisions (missing values).

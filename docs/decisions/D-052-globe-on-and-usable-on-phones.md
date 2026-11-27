# D-052 The globe goes on in production now, Plotly 3D goes, and the tracker is made usable on phones

**Status:** Accepted · **Date:** 2026-11-27 · **PRs:** this PR (`feature/globe-usable`)
**Component:** the tracker page, the Cesium viewer, the filter panel, search · **Tier:** full (production's view changes)

## Context

After #84 (3.3b) went live, the owner found production close to unusable, especially on a phone (Galaxy-class,
Adreno 740): the Plotly 3D view's zoom was jerky, the page was slow to start and to switch tabs, opening Filters
lagged, and a filter change took 2-3 s. Measurements on 27 Nov 2026 (full production data, a phone-sized page with
Chrome's CPU slowed 4x, and the owner's phone over the home network):

- Every tab was rendered at once: with the globe open, the Plotly 3D scene and the 2D map's WebGL canvas were in the
  page too. The 3D tab re-sent its whole figure (4.3 MB) and the list (4.0 MB) on every visit.
- The two search dropdowns put ~19,800 names and ~19,800 SATCAT numbers into the page (most of its 2.4 MB). Dash 4's
  dropdown spent 5.0 s of main-thread time on them in the first 30 s, and Dash re-read them on every update.
- Opening Filters was a server round trip; a filter change took 5.7 s from click to dots, of which the server used
  0.08 s and the globe 0.5-0.8 s; the rest was the page's main thread, busy 98% of the time because the globe drew
  every frame.
- On the phone: 23 fps, 4.9 ms per frame moving the dots. Moving them less often made no difference (tested with the
  owner), so the cost was the drawing, not the interpolation.
- A fix for the 3D view's zoom snapping back on its 20 s refresh was built and dropped: at full scale it changed
  little, because every zoom step redraws ~16,600 points.

The owner chose (27 Nov 2026): stop Plotly performance work; bring the globe in now in one PR, ahead of 3.13/3.14
and ahead of 3.4/3.5; remove Plotly 3D even though orbit paths only return in 3.4; hover labels in this PR; search as
a browsable list (option A, roadmap 3.9's list built early); a loading bar; shade 2 for the Earth; darker, smaller
dots; the panel's colours matching the globe's.

## Options

| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **Globe on by default, Plotly 3D removed, the rest made usable now (chosen)** | Fixes production's main view; one view to make fast | Orbit paths gone until 3.4; a bigger PR than the one-task rule | 3.4 adds selection and paths to the globe; 3.6 removes the 2D map |
| Switch the flag on and keep Plotly 3D beside the globe | Nothing lost | Keeps the slowest view and its 20 s server propagation in the page; two 3D views | Delays 3.6's clean-up |
| Keep improving Plotly 3D | No new view for visitors | Measured: the redraw cost of ~16,600 points can't be patched away | Work thrown away at 3.6 |
| Search: type-only server search (PR #73's approach) | Smallest change | Owner rejected it on 24 Nov (browse-first, children and casual users) | - |
| Search: load the full dropdown lists on first open | Keeps Dash dropdowns | First open still freezes for seconds on a phone | Replaced at 3.9 anyway |
| Search: a browsable list built in the page from a compact dataset (chosen) | Removes ~40,000 options from the page; browse and type; one source of truth | A new derived dataset to serve | It is 3.9's list; fly-to and Save image follow in 3.9 |

## Decision

1. **The globe is on unless `SATTRACK_CESIUM_VIEWER` switches it off** (`0`, `false`, `no`, `off`). The variable stays
   as an off switch until 3.6 removes it. Switched off, or without verified vendor files, the tracker opens on the
   list. The tab is "Globe" (no "beta"). Merging this PR therefore switches the globe on in production.
2. **The Plotly 3D view is removed**: callback, tab, 20 s timer, stores, helpers, the Earth image and Pillow.
3. **Only the open tab holds a view.** The 2D map is built when its tab opens and removed when it closes, with its
   timer on only while open, so Plotly's script loads only then. The list is built while open and isn't re-sent
   when the filters haven't changed (`list-shown-spec`).
4. **Search is a browsable list drawn in the page** (`assets/07_search.js`) from `/data/search.json`, which the app
   derives from the objects dataset at start-up (`app/core/search_index.py`): one record per object with the objects
   dataset's field names, and its envelope's attribution and caution, ordered space stations first, then payloads,
   then the other types, newest launches first within each. Typing a name or SATCAT number narrows it. A pick sets
   the hidden `satcatid-filter-dropdown` value the panel already reads (ids kept); its chip names the satellite.
   Unlike roadmap 3.9's note, the list is built from a server-derived dataset rather than in the viewer's worker, so
   it works whether or not the globe is on and doesn't add work to the worker's start-up.
5. **Opening Filters runs in the browser** (a clientside callback).
6. **The globe draws on demand** (Cesium's request-render mode): when the camera moves, a filter applies, a label
   shows, or simulation time has moved on by 0.25 s, about 4 draws a second at 1x when untouched; gestures draw
   every frame as before (30 fps cap on touch screens, D-027). The step controller and the slow-device hint use only
   continuous frames.
7. **Look:** the Earth's imagery dimmed (brightness 0.55, contrast 1.2, saturation 0.8, gamma 1.1: the owner's
   "shade 2"), no ground or sky atmosphere, a navy base colour (`--st-globe-base`) before the imagery arrives; dots
   3 px with distance scaling; `--st-active` #e8564a instead of #f07a6e (read as pink). The type switches lose their
   type-colour swatches; a key under Status shows Active and Inactive. Type colours stay in the tokens for 3.13.
8. **Hover labels** (3.4's first tier, pulled forward): name, SATCAT number, type, status, orbit class, launch year
   and owner, from the worker's records; a tap shows it on touch screens; one pick per 100 ms; hidden while dragging
   and when the camera moves.
9. **A loading bar** is rendered with the page inside `div#globe` (its only Dash-rendered content, an amendment to
   D-013's "empty div"); the viewer fills one bar per start-up step and hides it when the satellites are placed.

## Evidence

Same machine, full production data (run_2026-11-26T031742Z), phone-sized page, CPU slowed 4x, software WebGL:

| | Before | After |
|---|---|---|
| Main thread in long tasks once started | 98% | 32% (full data), 0% (CI's synthetic catalogue, 10-20 s after load) |
| Dash dropdown main-thread time, first 30 s | 5.0 s | 0.2 s |
| Tracker page DOM after load | 576 nodes, 2.4 MB page response | 521 nodes, ~34 KB of markup |
| Opening Filters | 2.5 s | 0.8-0.9 s |
| Filter change, click to dots | 5.7 s | 1.1-1.5 s |
| Idle globe draws | every frame | 3.8 a second |
| Search data | ~40,000 options in the page | 169 KB Brotli, fetched after first positions |

Server-side, the spec and its validation take 22-30 ms and the panel summary 44-51 ms on the full data. The new
`test_phone_budget` holds the three phone limits in CI; the production-controls guard checks every visible control
against the globe, the type switches and Space junk mode included.

## Consequences

- Production shows the globe after merge. D-041's report-only Content-Security-Policy and HSTS (max-age one day)
  go live with it.
- Clicking a satellite for its orbit path is gone until 3.4; the 2D map's ground track stays (pick a satellite).
- `/data/search.json` is an app-derived dataset (not published by the pipeline), documented in
  `docs/app-data-contract.md`.
- The PR is larger than the one-task rule (the owner asked for one usable release).

## Revisit when

- D-041's trigger fires with this merge: confirm HSTS on `www.sattrackapp.com` and the apex, then raise max-age.
- The owner's phone still lags on gestures: profile on the device (remote debugging); options are a lower
  `resolutionScale`, fewer imagery tiles (`maximumScreenSpaceError`), or GPU interpolation (D-027).
- Start-up stays slow: the tracker page itself arrives through the router's callback after Dash loads (6.8 s before
  the viewer starts at 4x CPU in CI); serving the tracker's layout directly would remove that round trip.
- 3.9 builds fly-to: reuse this list; reconsider moving it into the worker only if measurements favour it.

## Related

D-013, D-016, D-021, D-027, D-041, D-044, D-049, D-050, D-051; roadmap 3.3b, 3.4, 3.6, 3.9, 3.13.

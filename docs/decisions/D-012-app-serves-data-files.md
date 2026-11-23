# D-012 The app serves the data files, with threaded workers; no extra CDN account

**Status:** Accepted · **Date:** 2026-11-22 · **PRs:** #57 (decision), #58 (plan 2.1), #59 (control, closed)
**Component:** delivery of the data files; `Procfile` · **Tier:** full

## Context
The S3 bucket is private and also holds the warehouse, logs and state. Heroku's router buffers only 1 MB of each
response; gunicorn's default sync workers (2) handle one request each, so a download the buffers can't absorb holds a
whole worker until the client has read it.

## Options
| Option | For | Against | Fit with planned features |
|---|---|---|---|
| **App serves pre-compressed files with an ETag; gunicorn `--threads 4`** | No AWS changes; bucket stays private; file always from the same run as the CSV; local and CI work the same | The app's memory holds ≈4.1 MB of compressed bytes per worker | Feature datasets add files through the same manifest |
| Cloudflare in front | Global caching | One more account and a DNS move to maintain (owner rejected the overhead) | – |
| Public S3 file or CloudFront now | Offloads the app | New AWS resources, CORS, cache invalidation; no need at today's traffic | The revisit path if traffic grows |
| Short-lived S3 links | Bucket stays private | CORS on the private bucket; links break on key rotation; awkward caching | – |
| Split files below 1 MB | Fits the router buffer | Multi-part loads add failure modes | – |

## Decision
The pipeline writes the pre-compressed file beside the CSV, listed in `app/current.json`. The app loads it at start-up
and serves it with an ETag, RFC 9110 encoding negotiation and weak revalidation. gunicorn runs `--threads 4`.

## Evidence
CI build check, 22 Nov (PR #59 control): with sync workers, four slow downloads of a 3 MB file blocked nothing (socket
buffers took it all; pages answered in 1 ms), but a 24 MB file held both workers and a page request timed out after
20 s. With `--threads 4`, pages answered in 1 ms during the 24 MB downloads.

## Consequences
CI's build check tests slow clients at 24 MB, a size that does block sync workers. Self-hosting Cesium (Cesium
decisions) adds ~2 MB of static files per new visitor, served the same way with long-lived caching.

## Revisit when
- Traffic needs a CDN (e.g. launch posts): AWS CloudFront in the existing account through CloudFormation, no new
  account, no DNS change.
- Data files grow past ~10 MB (all `object_detail` records ≈ 8–15 MB): re-check worker memory and download times.

## Related
D-009, D-010; the Cesium decisions (self-hosting).

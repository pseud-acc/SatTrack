#!/usr/bin/env bash
# Build the checked-out commit the way Heroku builds sattrackapp, run it the way a dyno runs it, and check it
# serves. Replaces the manual temp-app test: no Heroku account, API key or secret is involved.
#
#   1. Source = the committed tree only (`git archive HEAD`, what `git push heroku` sends), then .slugignore
#      applied, as Heroku does before the buildpack runs.
#   2. Build = Heroku's classic heroku/python buildpack (the one sattrackapp uses) inside Heroku's own
#      heroku-24 build image: bin/detect, then bin/compile <build> <cache> <env>.
#   3. Run = the Procfile `web` command in Heroku's heroku-24 runtime image, with .profile.d sourced and the
#      Eco dyno's 512 MB memory limit, PORT set like a dyno. The app reads the committed data sample
#      tests/app_data (SATTRACK_APP_DATA_DIR) instead of S3: CI has no AWS access.
#   4. Checks = the pages the manual test checked, no pipeline packages in the slug, slug size under Heroku's
#      limit, the app's data-load log line, no traceback, not killed for memory.
#
# Pins: the buildpack tag AND its commit (the clone fails if the tag moves), both images by digest.
# When Heroku ships a newer buildpack (https://github.com/heroku/heroku-buildpack-python/releases), bump
# BUILDPACK_TAG + BUILDPACK_SHA together; the job prints a notice when the pin is behind the latest release.
# Runs on GitHub's ubuntu runners (docker preinstalled); locally it needs bash, git, docker and curl.
set -euo pipefail

BUILDPACK_REPO=https://github.com/heroku/heroku-buildpack-python
BUILDPACK_TAG=v362
BUILDPACK_SHA=e5d67bcb895f7a128cd91a3747e31146b5e2bc52
BUILD_IMAGE=heroku/heroku:24-build@sha256:4944dc047119cfd7056a31a12d23171e2cb9f12147850e212128b6bd9f20517d
RUN_IMAGE=heroku/heroku:24@sha256:59837688d73d8f5240b72d5b9a801190674fcaeec831501dc709bf7999c7399f
SLUG_LIMIT_MB=500        # Heroku's hard limit on the compressed slug
PAGES=("/" "/_dash-layout" "/_dash-dependencies" "/sat_visualisation")
PORT=5000
# Heroku sets WEB_CONCURRENCY from the dyno memory (vendor/WEB_CONCURRENCY.sh: 512 MB / 256 MB per worker = 2),
# reading a cgroup v1 file that GitHub runners (cgroup v2) lack; set the value it computes on an Eco dyno.
WEB_CONCURRENCY=2
NAME=sattrack-ci-dyno
APP_DATA=tests/app_data  # mounted read-only into the dyno; never in the slug (.slugignore drops tests/)

W="${RUNNER_TEMP:-$(mktemp -d)}/heroku-build"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
rm -rf "$W" && mkdir -p "$W/app" "$W/cache" "$W/env" "$W/buildpack"
FAIL=0
fail() { echo "::error::$1"; FAIL=1; }

echo "::group::Source (git archive HEAD + .slugignore)"
git -C "$REPO_ROOT" archive --format=tar HEAD | tar -x -C "$W/app"
if [ -f "$W/app/.slugignore" ]; then
  # sattrackapp's patterns are top-level folders; each line is removed relative to the app root.
  while IFS= read -r pat || [ -n "$pat" ]; do
    pat="${pat%%#*}"; pat="$(echo "$pat" | xargs)"; [ -z "$pat" ] && continue
    case "$pat" in *..*) fail ".slugignore pattern '$pat' not supported"; continue;; esac
    ( cd "$W/app" && rm -rf -- ${pat#/} ) && echo "removed $pat"
  done < "$W/app/.slugignore"
fi
echo "::endgroup::"

echo "::group::Buildpack $BUILDPACK_TAG"
git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$BUILDPACK_TAG" "$BUILDPACK_REPO" "$W/buildpack"
got="$(git -C "$W/buildpack" rev-parse HEAD)"
[ "$got" = "$BUILDPACK_SHA" ] || { echo "::error::buildpack tag $BUILDPACK_TAG is $got, pinned $BUILDPACK_SHA"; exit 1; }
latest="$(git ls-remote --tags --refs "$BUILDPACK_REPO" | sed -n 's#.*\trefs/tags/v\([0-9][0-9]*\)$#\1#p' | sort -n | tail -1)"
[ "v$latest" = "$BUILDPACK_TAG" ] || echo "::notice::heroku-buildpack-python v$latest is out (pinned $BUILDPACK_TAG): Heroku builds with the latest, so bump the pin"
echo "::endgroup::"

echo "::group::Build (bin/compile in heroku-24-build)"
docker run --rm --user "$(id -u):$(id -g)" -e STACK=heroku-24 -e HOME=/tmp \
  -v "$W/app:/app" -v "$W/cache:/cache" -v "$W/env:/env:ro" -v "$W/buildpack:/buildpack" \
  "$BUILD_IMAGE" bash -c '/buildpack/bin/detect /app && /buildpack/bin/compile /app /cache /env' 2>&1 | tee "$W/build.log"
echo "::endgroup::"

echo "::group::Slug checks"
if find "$W/app/.heroku" -maxdepth 6 -type d \( -iname 'dbt*' -o -iname 'duckdb*' \) | grep -q .; then
  fail "pipeline packages (dbt/duckdb) are in the slug"
else
  echo "ok: no pipeline packages"
fi
slug_mb=$(( $(tar -czf - -C "$W/app" . | wc -c) / 1000000 ))
echo "slug (compressed): ${slug_mb} MB of ${SLUG_LIMIT_MB} MB"
[ "$slug_mb" -lt "$SLUG_LIMIT_MB" ] || fail "slug ${slug_mb} MB is over Heroku's ${SLUG_LIMIT_MB} MB limit"
echo "::endgroup::"

echo "::group::Run (Procfile web in heroku-24, 512 MB)"
CMD="$(sed -n 's/^web:[[:space:]]*//p' "$W/app/Procfile")"
[ -n "$CMD" ] || { echo "::error::no web process in Procfile"; exit 1; }
echo "web: $CMD"
docker run -d --name "$NAME" --memory 512m --memory-swap 512m --user "$(id -u):$(id -g)" \
  -e PORT="$PORT" -e DYNO=web.1 -e WEB_CONCURRENCY="$WEB_CONCURRENCY" -e HOME=/app -p "127.0.0.1:$PORT:$PORT" -v "$W/app:/app" -w /app \
  -e SATTRACK_APP_DATA_DIR=/app-data -v "$REPO_ROOT/$APP_DATA:/app-data:ro" \
  "$RUN_IMAGE" bash -c 'for f in /app/.profile.d/*.sh; do [ -f "$f" ] && . "$f"; done; exec '"$CMD" >/dev/null
up=0
for _ in $(seq 1 90); do
  [ "$(docker inspect -f '{{.State.Running}}' "$NAME")" = true ] || break
  [ "$(curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:$PORT/")" = 200 ] && { up=1; break; }
  sleep 2
done
[ "$up" = 1 ] || fail "app did not serve / within 180 s"
echo "::endgroup::"

echo "::group::Page checks"
if [ "$up" = 1 ]; then
  for p in "${PAGES[@]}"; do
    c="$(curl -s -o /dev/null -m 120 -w '%{http_code}' "http://127.0.0.1:$PORT$p")"
    echo "$c $p"; [ "$c" = 200 ] || fail "$p returned $c"
  done
fi
sleep 3
docker logs "$NAME" > "$W/run.log" 2>&1 || true
grep -E "Starting gunicorn|Booting worker|Data source|Satellite catalogue size" "$W/run.log" || true
loads=$(grep -c "Satellite catalogue size" "$W/run.log" || true)
[ "$loads" -ge "$WEB_CONCURRENCY" ] || fail "$loads of $WEB_CONCURRENCY workers logged their data load"
grep -q "Traceback" "$W/run.log" && { fail "traceback in the app log"; cat "$W/run.log"; }
[ "$(docker inspect -f '{{.State.OOMKilled}}' "$NAME")" = false ] || fail "killed for exceeding 512 MB"
echo "::endgroup::"

[ "$FAIL" = 0 ] && echo "RESULT: PASS" || { echo "RESULT: FAIL"; exit 1; }

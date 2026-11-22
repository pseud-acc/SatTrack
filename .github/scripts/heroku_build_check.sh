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
#   5. Data files = /data/objects.json served pre-compressed (Brotli or gzip) with an ETag and 304 on revalidation;
#      and slow clients: 4 rate-limited downloads of a 24 MB file run while pages are requested. With threaded
#      workers (Procfile --threads, decision D-012) the pages still answer. The size matters: a control run with
#      sync workers (PR #59) showed a 3 MB file is absorbed by socket buffers and blocks nothing, while 24 MB holds
#      both workers and the page request times out, so this check can fail.
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
APP_DATA=tests/app_data  # copied and mounted read-only into the dyno; never in the slug (.slugignore drops tests/)
SLOW_FILE_MB=24          # the slow-client test's dataset (CI only): larger than socket buffers can absorb (see 5.)

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
# The committed sample plus, for the slow-client check, a CI-only dataset of random bytes served as gzip.
mkdir -p "$W/app-data" && cp -r "$REPO_ROOT/$APP_DATA/." "$W/app-data/"
head -c $((SLOW_FILE_MB * 1000000)) /dev/urandom > "$W/app-data/slowtest.json.gz"
CMD="$(sed -n 's/^web:[[:space:]]*//p' "$W/app/Procfile")"
[ -n "$CMD" ] || { echo "::error::no web process in Procfile"; exit 1; }
echo "web: $CMD"
docker run -d --name "$NAME" --memory 512m --memory-swap 512m --user "$(id -u):$(id -g)" \
  -e PORT="$PORT" -e DYNO=web.1 -e WEB_CONCURRENCY="$WEB_CONCURRENCY" -e HOME=/app -p "127.0.0.1:$PORT:$PORT" -v "$W/app:/app" -w /app \
  -e SATTRACK_APP_DATA_DIR=/app-data -v "$W/app-data:/app-data:ro" \
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
# Count matches, not lines: two workers can print onto the same line.
loads=$({ grep -o "Satellite catalogue size" "$W/run.log" || true; } | wc -l)
[ "$loads" -ge "$WEB_CONCURRENCY" ] || fail "$loads of $WEB_CONCURRENCY workers logged their data load"
grep -q "Traceback" "$W/run.log" && { fail "traceback in the app log"; cat "$W/run.log"; }
[ "$(docker inspect -f '{{.State.OOMKilled}}' "$NAME")" = false ] || fail "killed for exceeding 512 MB"
echo "::endgroup::"

echo "::group::Data files (/data/objects.json, slow clients)"
if [ "$up" = 1 ]; then
  URL="http://127.0.0.1:$PORT/data/objects.json"
  hdr() { grep -i "^$1:" "$2" | head -1 | cut -d' ' -f2- | tr -d '\r'; }
  code="$(curl -s -o "$W/objects.br" -D "$W/h_br" -H 'Accept-Encoding: br' -w '%{http_code}' "$URL")"
  enc="$(hdr Content-Encoding "$W/h_br")"; etag="$(hdr ETag "$W/h_br")"
  echo "br: $code $enc $(wc -c < "$W/objects.br") bytes, ETag $etag"
  [ "$code" = 200 ] && [ "$enc" = br ] && [ -n "$etag" ] || fail "objects.json not served as Brotli with an ETag"
  code="$(curl -s -o "$W/objects.gz" -D "$W/h_gz" -H 'Accept-Encoding: gzip' -w '%{http_code}' "$URL")"
  echo "gzip: $code $(hdr Content-Encoding "$W/h_gz")"
  [ "$code" = 200 ] && [ "$(hdr Content-Encoding "$W/h_gz")" = gzip ] || fail "objects.json not served as gzip"
  count="$(gzip -dc "$W/objects.gz" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["count"]==len(d["records"]); print(d["count"])' 2>&1)"     || fail "objects.json is not a valid dataset: $count"
  echo "records: $count"
  code="$(curl -s -o /dev/null -H 'Accept-Encoding: br' -H "If-None-Match: $etag" -w '%{http_code}' "$URL")"
  echo "revalidate: $code"; [ "$code" = 304 ] || fail "If-None-Match did not return 304"
  # Slow clients: 4 downloads at 30 KB/s keep their connections busy far longer than the page checks below.
  # First prove the test file is really served in full, else "slow" downloads could end at once (a 404) and the
  # check would pass with idle workers (Copilot review on #58).
  SLOW_URL="http://127.0.0.1:$PORT/data/slowtest.json"
  got="$(curl -s -o /dev/null -m 60 -H 'Accept-Encoding: gzip' -w '%{http_code} %{size_download}' "$SLOW_URL" || true)"
  echo "slow-test file: $got (expect 200 $((SLOW_FILE_MB * 1000000)))"
  [ "$got" = "200 $((SLOW_FILE_MB * 1000000))" ] || fail "slow-test file not served in full ($got)"
  pids=()
  for _ in 1 2 3 4; do
    curl -s -o /dev/null -m 150 --limit-rate 30k -H 'Accept-Encoding: gzip' "$SLOW_URL" &
    pids+=($!)
  done
  sleep 3
  still_running() {   # every slow download must still be in progress, or the timings below prove nothing
    local n=0; for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null && n=$((n + 1)); done
    echo "slow downloads still running ($1): $n of ${#pids[@]}"
    [ "$n" = "${#pids[@]}" ] || fail "slow downloads ended early ($1): the check would not load the workers"
  }
  still_running "before page checks"
  for p in /_dash-layout /_dash-dependencies; do
    t="$(curl -s -o /dev/null -m 20 -w '%{http_code} %{time_total}' "http://127.0.0.1:$PORT$p" || true)"
    echo "during slow downloads: $p -> $t s"
    [ "${t%% *}" = 200 ] && awk -v s="${t##* }" 'BEGIN { exit !(s < 5) }' \
      || fail "$p waited behind slow downloads ($t): workers are blocked"
  done
  still_running "after page checks"
  kill "${pids[@]}" 2>/dev/null || true; wait 2>/dev/null || true
fi
echo "::endgroup::"

[ "$FAIL" = 0 ] && echo "RESULT: PASS" || { echo "RESULT: FAIL"; exit 1; }

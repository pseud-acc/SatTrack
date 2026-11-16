#!/usr/bin/env bash
# Deploy the checked-out commit to Heroku through the Platform API's Build API, then check the live app.
# Called by .github/workflows/heroku-deploy.yml (environment `heroku`, main only).
#
#   1. Source = `git archive HEAD` as a tarball (what `git push heroku` sends; Heroku applies .slugignore).
#      No git history is needed, so the job never clones the repo's history.
#   2. POST /sources for an upload slot, PUT the tarball, POST /apps/<app>/builds with the commit SHA as the
#      version; the build output streams into this log.
#   3. Wait for the build and its release to succeed and for the web dyno to run that release.
#   4. Check the live site serves, and count (never print) the app's "Data source: s3" log lines, so a release
#      that cannot read S3 fails the job. App log lines name the bucket and object versions, so they stay out
#      of the public Actions log.
#
# Env: HEROKU_API_KEY (secret: a deploy-only account's token), HEROKU_APP, SITE_URL. Needs bash, git, curl, jq.
set -euo pipefail
: "${HEROKU_APP:?}" "${SITE_URL:?}"
[ -n "${HEROKU_API_KEY:-}" ] || { echo "::error::HEROKU_API_KEY is not set in the 'heroku' environment"; exit 1; }

API=https://api.heroku.com
SHA="$(git rev-parse HEAD)"
TMP="${RUNNER_TEMP:-$(mktemp -d)}"
PAGES=("/" "/_dash-layout" "/_dash-dependencies" "/sat_visualisation")
api() {
  curl -sS --fail-with-body -H "Accept: application/vnd.heroku+json; version=3" \
    -H "Authorization: Bearer $HEROKU_API_KEY" -H "Content-Type: application/json" "$@"
}

echo "::group::Upload source ($SHA)"
git archive --format=tar.gz -o "$TMP/source.tgz" HEAD
echo "source tarball: $(( $(wc -c < "$TMP/source.tgz") / 1000 )) kB"
src="$(api -X POST "$API/sources")"
get_url="$(jq -r .source_blob.get_url <<<"$src")"; put_url="$(jq -r .source_blob.put_url <<<"$src")"
echo "::add-mask::$get_url"; echo "::add-mask::$put_url"   # short-lived presigned URLs
curl -sS --fail -X PUT -H "Content-Type:" --data-binary @"$TMP/source.tgz" "$put_url"
echo "::endgroup::"

echo "::group::Build on Heroku"
body="$(jq -n --arg url "$get_url" --arg v "$SHA" '{source_blob: {url: $url, version: $v}}')"
build="$(api -X POST "$API/apps/$HEROKU_APP/builds" -d "$body")"
build_id="$(jq -r .id <<<"$build")"
stream="$(jq -r .output_stream_url <<<"$build")"; echo "::add-mask::$stream"
curl -sS -N --max-time 1500 "$stream" || true
status=pending
for _ in $(seq 1 90); do
  status="$(api "$API/apps/$HEROKU_APP/builds/$build_id" | jq -r .status)"
  [ "$status" = pending ] || break; sleep 10
done
echo "::endgroup::"
[ "$status" = succeeded ] || { echo "::error::Heroku build $status"; exit 1; }

echo "::group::Release"
release_id="$(api "$API/apps/$HEROKU_APP/builds/$build_id" | jq -r .release.id)"
rstatus=pending
for _ in $(seq 1 60); do
  rel="$(api "$API/apps/$HEROKU_APP/releases/$release_id")"; rstatus="$(jq -r .status <<<"$rel")"
  [ "$rstatus" = pending ] || break; sleep 5
done
[ "$rstatus" = succeeded ] || { echo "::error::release $rstatus"; exit 1; }
version="$(jq -r .version <<<"$rel")"
released_at="$(jq -r .updated_at <<<"$rel")"
echo "released v$version for $SHA"
# Wake the (possibly sleeping) Eco dyno, then wait until the web dyno is up on this release.
curl -s -o /dev/null -m 60 "$SITE_URL/" || true
up=0
for _ in $(seq 1 36); do
  if api "$API/apps/$HEROKU_APP/dynos" | jq -e --argjson v "$version" \
      'any(.[]; .type == "web" and .state == "up" and .release.version == $v)' >/dev/null; then up=1; break; fi
  sleep 5
done
echo "::endgroup::"
[ "$up" = 1 ] || { echo "::error::no web dyno up on v$version after 3 minutes"; exit 1; }

echo "::group::Live checks ($SITE_URL)"
FAIL=0
for p in "${PAGES[@]}"; do
  c=000
  for _ in 1 2 3 4 5 6; do
    c="$(curl -s -o /dev/null -m 60 -w '%{http_code}' "$SITE_URL$p")"; [ "$c" = 200 ] && break; sleep 10
  done
  echo "$c $p"; [ "$c" = 200 ] || { echo "::error::$p returned $c"; FAIL=1; }
done
# App log lines since this release: count S3 data loads (2 workers) without printing the lines.
loads=0
for _ in $(seq 1 12); do
  logurl="$(api -X POST "$API/apps/$HEROKU_APP/log-sessions" -d '{"lines": 1500, "source": "app"}' | jq -r .logplex_url)"
  echo "::add-mask::$logurl"
  loads="$(curl -sS -m 30 "$logurl" | awk -v t="$released_at" '$1 >= t' \
           | { grep -o "Data source: s3 (Space-Track + GCAT)" || true; } | wc -l)"
  [ "$loads" -ge 1 ] && break; sleep 10
done
echo "workers that loaded S3 data since v$version: $loads"
[ "$loads" -ge 1 ] || { echo "::error::no 'Data source: s3' line in the app log since v$version"; FAIL=1; }
echo "::endgroup::"

[ "$FAIL" = 0 ] && echo "DEPLOYED: v$version ($SHA)" || exit 1

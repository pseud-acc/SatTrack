#!/usr/bin/env bash
# Build the mart entity relationship diagram for the docs site from the dbt manifest.
#
#   scripts/erd/build_erd.sh <target_dir> <site_dir>
#
# <target_dir>  dbt target dir holding manifest.json and catalog.json (docs generate --write-catalog)
# <site_dir>    the docs site; the diagram files are written to <site_dir>/erd/:
#                 erd_marts.mmd  Mermaid, key columns only (PK / FK)
#                 erd_marts.dbml DBML, all columns
#                 erd_marts.svg  rendered Mermaid
#
# The relationships are the `fk__*` relationships tests on the marts (dbterd reads them from the manifest); no
# database is read. Fails when dbterd finds no relationship, so a renamed test cannot publish an empty diagram.
#
# ERD_RENDER picks the SVG renderer:
#   npx   (default) the pinned @mermaid-js/mermaid-cli with the Chrome on the runner (CI)
#   edge  scripts/erd/mermaid_to_svg_edge.py, headless Edge on Windows (local, no Node needed)
#   none  skip the SVG
# Needs dbterd and PyYAML in the Python environment (requirements-docs.txt).
set -euo pipefail

TARGET=${1:?usage: build_erd.sh <target_dir> <site_dir>}
SITE=${2:?usage: build_erd.sh <target_dir> <site_dir>}
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-python}
DBTERD=${DBTERD:-dbterd}
ERD_RENDER=${ERD_RENDER:-npx}
MERMAID_CLI=@mermaid-js/mermaid-cli@11.17.0   # published 2026-09-02
PUPPETEER=puppeteer@24.43.1                   # peer dependency of mermaid-cli, published 2026-05-11
export PYTHONUTF8=1

# Our foreign keys are relationships tests named fk__*, not the "relationship" name dbterd looks for by default.
ALGO='test_relationship:(name:fk__|c_from:column_name|c_to:field)'
SELECT=(-s schema:marts -s schema:marts_tracking)   # the marts only; -enf model: no entity-name filter

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$SITE/erd"

"$PY" "$HERE/sanitize_manifest.py" "$TARGET/manifest.json" "$WORK/manifest.json"
cp "$TARGET/catalog.json" "$WORK/catalog.json"

"$DBTERD" run -ad "$WORK" -t mermaid -a "$ALGO" "${SELECT[@]}" -enf model -o "$WORK" -ofn full.mmd
"$DBTERD" run -ad "$WORK" -t dbml -a "$ALGO" "${SELECT[@]}" -enf model -o "$SITE/erd" -ofn erd_marts.dbml

relationships=$(grep -cE '^\s+"\w+" \S+ "\w+": ' "$WORK/full.mmd" || true)
echo "relationships found: $relationships"
if [ "$relationships" -eq 0 ]; then
  echo "no fk__* relationships in the manifest" >&2
  exit 1
fi

"$PY" "$HERE/slim_mermaid.py" "$WORK/full.mmd" "$SITE/erd/erd_marts.mmd"

case "$ERD_RENDER" in
  npx)
    # Ubuntu runners block Chrome's sandbox for unprivileged users, and the runner is a throwaway VM that renders
    # only the diagram written above, so the sandbox is switched off for this one call.
    chrome=$(command -v google-chrome || command -v chromium || true)
    [ -n "$chrome" ] || { echo "no Chrome on this runner" >&2; exit 1; }
    cat > "$WORK/puppeteer.json" <<JSON
{"executablePath": "$chrome", "args": ["--no-sandbox"]}
JSON
    cat > "$WORK/mermaid.json" <<'JSON'
{"theme": "neutral", "er": {"useMaxWidth": false}}
JSON
    PUPPETEER_SKIP_DOWNLOAD=1 npx --yes --package="$MERMAID_CLI" --package="$PUPPETEER" mmdc \
      --input "$SITE/erd/erd_marts.mmd" --output "$SITE/erd/erd_marts.svg" \
      --puppeteerConfigFile "$WORK/puppeteer.json" --configFile "$WORK/mermaid.json" --backgroundColor white
    ;;
  edge)
    "$PY" "$HERE/mermaid_to_svg_edge.py" "$SITE/erd/erd_marts.mmd" "$SITE/erd/erd_marts.svg"
    ;;
  none)
    ;;
  *)
    echo "ERD_RENDER must be npx, edge or none" >&2
    exit 1
    ;;
esac

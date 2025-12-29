#!/bin/bash
# Sync dependencies: Install with Poetry and update requirements.txt
# Usage: ./sync_dependencies.sh

set -e  # Exit on error

echo "========================================"
echo "Syncing Dependencies"
echo "========================================"
echo ""

# 1. Install dependencies with Poetry
echo "📦 Installing dependencies with Poetry..."
poetry install
echo "✓ Dependencies installed"
echo ""

# 2. Export to requirements.txt
echo "📄 Updating requirements.txt..."
poetry export -f requirements.txt --output requirements_temp.txt --without-hashes --without dev

# 3. Clean version markers
python -c "import re; content = open('requirements_temp.txt').read(); open('requirements.txt', 'w').write(re.sub(r' ;.*', '', content))"
rm requirements_temp.txt

echo "✓ requirements.txt updated"
echo ""

# 4. Show what changed
if git diff --quiet requirements.txt 2>/dev/null; then
    echo "No changes to requirements.txt"
else
    echo "Changes to requirements.txt:"
    git diff requirements.txt 2>/dev/null || echo "  (git not available or file not tracked)"
fi
echo ""

# 5. Summary
echo "========================================"
echo "✓ Sync Complete!"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Dependencies installed from pyproject.toml"
echo "  - requirements.txt updated for Heroku"
echo ""
echo "Next steps:"
echo "  1. Review changes above"
echo "  2. Test your app: python run_app.py"
echo "  3. Commit if needed: git add requirements.txt && git commit -m 'chore: update requirements.txt'"
echo ""
echo "Note: GitHub Actions will also auto-sync requirements.txt when you push."

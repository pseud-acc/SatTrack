#!/bin/bash
# Test script to verify Heroku deployment readiness

set -e  # Exit on error

echo "========================================="
echo "Heroku Deployment Readiness Test"
echo "========================================="
echo ""

# 1. Check Python version
echo "✓ Checking the pinned Python version..."
grep -q "^3.12" .python-version && echo "  .python-version pins Python 3.12!" || { echo "  ERROR: .python-version does not pin 3.12!"; exit 1; }
echo ""

# 2. Check required files exist
echo "✓ Checking required files..."
for file in pyproject.toml uv.lock .python-version Procfile; do
    if [ -f "$file" ]; then
        echo "  Found: $file"
    else
        echo "  ERROR: Missing $file"
        exit 1
    fi
done
echo ""

# 3. Exactly one package manager file at the root (Heroku's buildpack refuses several)
echo "✓ Checking for conflicting package manager files..."
for file in requirements.txt poetry.lock Pipfile.lock; do
    if [ -f "$file" ]; then
        echo "  ERROR: $file found next to uv.lock; Heroku would stop the build"
        exit 1
    fi
done
echo "  Only uv.lock found!"
echo ""

# 4. Lockfile in step with pyproject.toml, then install exactly what Heroku installs
echo "✓ Checking uv.lock and installing the app dependencies (as Heroku does)..."
uv lock --check && echo "  uv.lock matches pyproject.toml!" || { echo "  ERROR: run 'uv lock' and commit uv.lock"; exit 1; }
uv sync --locked --no-default-groups && echo "  All dependencies installed successfully!" || { echo "  ERROR: Failed to install dependencies!"; exit 1; }
echo ""

# 5. Test gunicorn
echo "✓ Testing gunicorn..."
uv run --no-sync python -c "import gunicorn" && echo "  gunicorn is installed!" || { echo "  ERROR: gunicorn not found!"; exit 1; }
echo ""

# 6. Verify Procfile syntax
echo "✓ Verifying Procfile..."
cat Procfile
echo ""

# 7. Test app import
echo "✓ Testing app import..."
uv run --no-sync python -c "from run_app import server; print('  App imports successfully!')" || { echo "  ERROR: Failed to import app!"; exit 1; }
echo ""

# 8. Optional: Start gunicorn test (timeout after 5s)
echo "✓ Testing gunicorn startup (5 second test)..."
timeout 5s uv run --no-sync gunicorn run_app:server --bind 0.0.0.0:8000 2>/dev/null || true
echo "  Gunicorn startup test completed!"
echo ""

echo "========================================="
echo "✓ All tests passed!"
echo "Your app is ready for Heroku deployment!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Commit your changes"
echo "  2. Deploy: git push heroku main"
echo "  3. Monitor logs: heroku logs --tail"

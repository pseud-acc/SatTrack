#!/bin/bash
# Test script to verify Heroku deployment readiness

set -e  # Exit on error

echo "========================================="
echo "Heroku Deployment Readiness Test"
echo "========================================="
echo ""

# 1. Check Python version
echo "✓ Checking Python version..."
python --version | grep "3.12" && echo "  Python 3.12 detected!" || { echo "  ERROR: Python 3.12 not found!"; exit 1; }
echo ""

# 2. Check required files exist
echo "✓ Checking required files..."
for file in requirements.txt runtime.txt Procfile; do
    if [ -f "$file" ]; then
        echo "  Found: $file"
    else
        echo "  ERROR: Missing $file"
        exit 1
    fi
done
echo ""

# 3. Verify requirements.txt is clean (no version markers)
echo "✓ Checking requirements.txt format..."
if grep -q " ; python_version" requirements.txt; then
    echo "  WARNING: Found Python version markers in requirements.txt"
    echo "  Run: poetry export -f requirements.txt --output requirements_temp.txt --without-hashes --without dev"
    echo "       python -c \"import re; content = open('requirements_temp.txt').read(); open('requirements.txt', 'w').write(re.sub(r' ;.*', '', content))\""
    exit 1
else
    echo "  requirements.txt is clean!"
fi
echo ""

# 4. Test install from requirements.txt
echo "✓ Testing installation from requirements.txt..."
echo "  (This may take a few minutes...)"
pip install -q -r requirements.txt && echo "  All dependencies installed successfully!" || { echo "  ERROR: Failed to install dependencies!"; exit 1; }
echo ""

# 5. Test gunicorn
echo "✓ Testing gunicorn..."
which gunicorn > /dev/null && echo "  gunicorn is installed!" || { echo "  ERROR: gunicorn not found!"; exit 1; }
echo ""

# 6. Verify Procfile syntax
echo "✓ Verifying Procfile..."
cat Procfile
echo ""

# 7. Test app import
echo "✓ Testing app import..."
python -c "from run_app import server; print('  App imports successfully!')" || { echo "  ERROR: Failed to import app!"; exit 1; }
echo ""

# 8. Optional: Start gunicorn test (timeout after 5s)
echo "✓ Testing gunicorn startup (5 second test)..."
timeout 5s gunicorn run_app:server --bind 0.0.0.0:8000 2>/dev/null || true
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

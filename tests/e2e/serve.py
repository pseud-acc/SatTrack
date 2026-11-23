"""Serve the app for the browser tests: the committed sample, the clock frozen at the sample's download time
(as in tests/app), on 127.0.0.1:<port>. Started by tests/e2e/conftest.py; not for production.

Usage: python tests/e2e/serve.py <port>
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(REPO_ROOT / "tests" / "app")]
os.environ.pop("SATTRACK_S3_BUCKET", None)
# SATTRACK_E2E_DATA_DIR: a copy of the sample with a bigger objects dataset (the viewer's budget checks)
os.environ["SATTRACK_APP_DATA_DIR"] = os.environ.get("SATTRACK_E2E_DATA_DIR") or str(REPO_ROOT / "tests" / "app_data")
os.chdir(REPO_ROOT)

from _support import frozen_datetime, reference_time  # noqa: E402

import app.helper.helper__app_data as app_data_helper  # noqa: E402

app_data_helper.datetime = frozen_datetime(reference_time())

import run_app  # noqa: E402

if __name__ == "__main__":
    run_app.app.run(host="127.0.0.1", port=int(sys.argv[1]), debug=False, threaded=True)

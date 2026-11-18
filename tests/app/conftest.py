"""Shared set-up for the app tests (run from the repo root: `uv run pytest tests/app`).

- Data: the committed sample in tests/app_data (from the pipeline's app export), never S3. SATTRACK_S3_BUCKET is
  removed so a developer's shell can't point a test run at the live bucket.
- Clock: the app's clock is frozen at the sample's Space-Track download time, so results don't depend on the
  day the tests run (otherwise ageing elements start failing to propagate and rows disappear).
- Working directory: the repo root, because the app opens its Earth map by a relative path.
"""
import json
import os
import sys

import pytest

from _support import APP_DATA_DIR, REPO_ROOT, CallbackCaller, frozen_datetime, load_sample, reference_time

os.environ.pop("SATTRACK_S3_BUCKET", None)
os.environ["SATTRACK_APP_DATA_DIR"] = str(APP_DATA_DIR)
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def sample_df():
    """The sample satellite catalogue as stored (tests must not modify it)."""
    return load_sample()


@pytest.fixture(scope="session")
def t_ref():
    return reference_time()


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch, t_ref):
    """The only clock the app reads in its request path is datetime.utcnow() in helper__app_data."""
    import app.helper.helper__app_data as app_data_helper
    monkeypatch.setattr(app_data_helper, "datetime", frozen_datetime(t_ref))


@pytest.fixture(scope="session")
def app_module():
    """run_app imported once, as gunicorn does: builds the Dash app, loads the sample, registers callbacks."""
    import run_app
    return run_app


@pytest.fixture(scope="session")
def client(app_module):
    return app_module.server.test_client()


@pytest.fixture(scope="session")
def dependencies(client):
    return json.loads(client.get("/_dash-dependencies").data)


@pytest.fixture(scope="session")
def callbacks(client, dependencies, app_module):
    return CallbackCaller(client, dependencies, app_module.app.validation_layout)

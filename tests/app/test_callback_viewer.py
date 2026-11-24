"""The viewer's clientside bridge callback (app/callbacks/callback_viewer.py), registered only with the viewer flag
on. It runs in the browser, so its behaviour is tested in tests/e2e/test_viewer.py; here: its wiring in the
flag-on app ('viewer-bridge' is its output), and that it never touches div#globe (D-013)."""
import pytest

from _viewer_support import flag_on_app, make_fake_vendor


@pytest.fixture(scope="module")
def deps(tmp_path_factory):
    return flag_on_app(make_fake_vendor(tmp_path_factory.mktemp("vendor")))["dependencies"]


def test_bridge_is_the_only_new_callback_and_is_clientside(deps):
    bridge = [d for d in deps if d["output"] == "viewer-bridge.data"]
    assert len(bridge) == 1
    d = bridge[0]
    assert d["clientside_function"] is not None   # runs in the browser, no server round trip
    assert [(x["id"], x["property"]) for x in d["inputs"]] == [("viewer-config", "data"), ("viewer-filters", "data")]
    assert not [x for x in d["inputs"] + d["state"] if x["id"] == "globe"]


def test_bridge_source_loads_the_module_and_writes_no_html():
    from app.callbacks.callback_viewer import BRIDGE
    assert 'type = "module"' in BRIDGE and "config.module" in BRIDGE
    assert "innerHTML" not in BRIDGE and "eval(" not in BRIDGE

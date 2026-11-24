"""Helpers for the Cesium viewer's server-side tests (roadmap 3.2).

- make_fake_vendor(): a small stand-in for static/vendor with a manifest for the committed vendor/cesium.lock, so
  the server side can be tested without downloading Cesium (the browser tests use the real files).
- flag_on_app(): the app built in a separate Python process with SATTRACK_CESIUM_VIEWER=1 (the flag is read when
  run_app is imported, and this test session imports it with the flag off, as production runs).
"""
import gzip
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = Path(__file__).with_name("_viewer_probe.py")


def make_fake_vendor(directory):
    import brotli

    directory = Path(directory)
    lock = (REPO_ROOT / "vendor" / "cesium.lock").read_bytes()
    files = {"cesium-1.147.0/index.js": b"export const CesiumWidget = 1;\n" * 50,
             "cesium-1.147.0/Assets/Textures/NaturalEarthII/0/0/0.jpg": b"\xff\xd8\xff fake jpeg",
             "satellite.js-7.1.0/dist/io.js": b"export function json2satrec() {}\n"}
    manifest = {"schema": 1, "lock_sha256": hashlib.sha256(lock).hexdigest(), "files": {},
                "packages": [{"name": "cesium", "version": "1.147.0", "dest": "cesium-1.147.0"},
                             {"name": "satellite.js", "version": "7.1.0", "dest": "satellite.js-7.1.0"}]}
    for rel, body in files.items():
        path = directory / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        entry = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "encodings": {}}
        if rel.endswith(".js") and len(body) > 200:
            for enc, suffix, comp in (("br", ".br", brotli.compress(body)), ("gzip", ".gz", gzip.compress(body))):
                (directory / (rel + suffix)).write_bytes(comp)
                entry["encodings"][enc] = {"sha256": hashlib.sha256(comp).hexdigest(), "bytes": len(comp)}
        manifest["files"][rel] = entry
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def flag_on_app(vendor_dir, flag="1"):
    """What the app serves with the viewer flag set to `flag` and `vendor_dir` as its vendor folder: see
    _viewer_probe.py for the keys."""
    env = dict(os.environ, SATTRACK_CESIUM_VIEWER=flag, SATTRACK_VENDOR_DIR=str(vendor_dir),
               SATTRACK_APP_DATA_DIR=str(REPO_ROOT / "tests" / "app_data"), PYTHONIOENCODING="utf-8")
    env.pop("SATTRACK_S3_BUCKET", None)
    out = subprocess.run([sys.executable, str(PROBE)], cwd=REPO_ROOT, env=env, capture_output=True, text=True,
                         encoding="utf-8", timeout=300)
    assert out.returncode == 0, out.stderr[-3000:]
    return json.loads(out.stdout.strip().splitlines()[-1])

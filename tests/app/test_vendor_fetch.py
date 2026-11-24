"""vendor/fetch.py (D-014): download, verify, extract, manifest. Offline: a synthetic npm tarball and a fake
downloader stand in for the registry. Also checks the committed vendor/cesium.lock itself."""
import base64
import hashlib
import importlib.util
import io
import json
import tarfile

import pytest

from _support import REPO_ROOT

spec = importlib.util.spec_from_file_location("vendor_fetch", REPO_ROOT / "vendor" / "fetch.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


def tarball(files, extra=()):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, body in files.items():
            info = tarfile.TarInfo(f"package/{name}")
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
        for info in extra:
            tar.addfile(info)
    return buf.getvalue()


def integrity(data):
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


FILES = {"LICENSE.md": b"licence " * 100, "Build/Cesium/index.js": b"export const a = 1;\n" * 400,
         "Build/Cesium/Workers/w.js": b"self.onmessage = null;\n" * 100, "Build/Cesium/Unused.js": b"unused",
         "Build/Cesium/Assets/Textures/NaturalEarthII/0/0/0.jpg": b"\xff\xd8 jpeg"}


def write_lock(tmp_path, data, url="https://registry.npmjs.org/cesium/-/cesium-1.0.0.tgz", files=None, patch=""):
    files = files or ['"LICENSE.md"', '"Build/Cesium/index.js"', '"Build/Cesium/Workers/*"',
                      '"Build/Cesium/Assets/Textures/NaturalEarthII/**"']
    lock = tmp_path / "cesium.lock"
    lock.write_text(f'''schema = 1
[[package]]
name = "cesium"
version = "1.0.0"
tarball = "{url}"
integrity = "{integrity(data)}"
dest = "cesium-1.0.0"
strip = "Build/Cesium/"
files = [{", ".join(files)}]
{patch}''', encoding="utf-8")
    return lock


PATCH = '''
[[package.patch]]
file = "index.js"
find = '(0,eval)("this")'
replace = "globalThis"
'''


def test_builds_the_listed_files_with_a_verified_manifest(tmp_path):
    data = tarball(FILES)
    lock, out = write_lock(tmp_path, data), tmp_path / "out"
    calls = []
    manifest = fetch.build(lock, out, tmp_path / "cache", fetch=lambda url: calls.append(url) or data)
    assert sorted(manifest["files"]) == ["cesium-1.0.0/Assets/Textures/NaturalEarthII/0/0/0.jpg",
                                         "cesium-1.0.0/LICENSE.md", "cesium-1.0.0/Workers/w.js",
                                         "cesium-1.0.0/index.js"]
    assert not (out / "cesium-1.0.0" / "Unused.js").exists()
    body = (out / "cesium-1.0.0" / "index.js").read_bytes()
    assert body == FILES["Build/Cesium/index.js"]
    entry = manifest["files"]["cesium-1.0.0/index.js"]
    assert entry["sha256"] == hashlib.sha256(body).hexdigest()
    assert set(entry["encodings"]) == {"br", "gzip"}
    assert "encodings" in manifest["files"]["cesium-1.0.0/Assets/Textures/NaturalEarthII/0/0/0.jpg"]
    assert fetch.verify(out, fetch.read_lock(lock)[1]) is None
    # a second run reuses the verified output: no download
    fetch.build(lock, out, tmp_path / "cache", fetch=lambda url: pytest.fail("downloaded again"))
    assert calls == ["https://registry.npmjs.org/cesium/-/cesium-1.0.0.tgz"]


def test_hash_mismatch_fails_and_keeps_the_previous_files(tmp_path):
    good = tarball(FILES)
    lock, out = write_lock(tmp_path, good), tmp_path / "out"
    fetch.build(lock, out, None, fetch=lambda url: good)
    tampered = tarball({**FILES, "Build/Cesium/index.js": b"evil()"})
    write_lock(tmp_path, good, files=['"LICENSE.md"', '"Build/Cesium/index.js"'])   # lock changes: must rebuild
    with pytest.raises(fetch.VendorError, match="integrity mismatch"):
        fetch.build(lock, out, None, fetch=lambda url: tampered)
    assert (out / "cesium-1.0.0" / "index.js").read_bytes() == FILES["Build/Cesium/index.js"]
    assert not (tmp_path / "out.tmp").exists()


def test_a_bad_cached_tarball_is_replaced(tmp_path):
    data = tarball(FILES)
    lock, cache = write_lock(tmp_path, data), tmp_path / "cache"
    cache.mkdir()
    (cache / "cesium-1.0.0.tgz").write_bytes(b"corrupt")
    fetch.build(lock, tmp_path / "out", cache, fetch=lambda url: data)
    assert (cache / "cesium-1.0.0.tgz").read_bytes() == data


def test_check_detects_a_changed_file(tmp_path):
    data = tarball(FILES)
    lock, out = write_lock(tmp_path, data), tmp_path / "out"
    fetch.build(lock, out, None, fetch=lambda url: data)
    (out / "cesium-1.0.0" / "Workers" / "w.js").write_bytes(b"changed")
    assert "differs" in fetch.verify(out, fetch.read_lock(lock)[1])
    assert fetch.main(["--check", "--out", str(out), "--lock", str(lock)]) == 1


def test_a_pattern_matching_nothing_fails(tmp_path):
    data = tarball(FILES)
    lock = write_lock(tmp_path, data, files=['"Build/Cesium/Cesium.js"'])
    with pytest.raises(fetch.VendorError, match="no files match"):
        fetch.build(lock, tmp_path / "out", None, fetch=lambda url: data)


@pytest.mark.parametrize("name", ["../evil.js", "Build/Cesium/../../evil.js"])
def test_unsafe_paths_are_refused(tmp_path, name):
    data = tarball({name: b"x"})
    lock = write_lock(tmp_path, data, files=['"**"'])
    with pytest.raises(fetch.VendorError, match="unsafe path"):
        fetch.build(lock, tmp_path / "out", None, fetch=lambda url: data)


def test_symlinks_are_refused(tmp_path):
    link = tarfile.TarInfo("package/Build/Cesium/index.js")
    link.type, link.linkname = tarfile.SYMTYPE, "/etc/passwd"
    data = tarball({}, extra=[link])
    lock = write_lock(tmp_path, data, files=['"Build/Cesium/index.js"'])
    with pytest.raises(fetch.VendorError, match="not a regular file"):
        fetch.build(lock, tmp_path / "out", None, fetch=lambda url: data)


def test_only_the_npm_registry_over_https(tmp_path):
    for url in ("http://registry.npmjs.org/x.tgz", "https://cdn.jsdelivr.net/npm/cesium.tgz"):
        with pytest.raises(fetch.VendorError, match="refusing"):
            fetch.download(url)


def test_glob_semantics():
    assert fetch.glob_regex("Workers/*").match("Workers/a.js")
    assert not fetch.glob_regex("Workers/*").match("Workers/sub/a.js")
    assert fetch.glob_regex("A/**").match("A/b/c/d.jpg")


def test_committed_lock_pins_exact_versions_from_the_registry():
    lock, _ = fetch.read_lock()
    pkgs = {p["name"]: p for p in lock["package"]}
    assert pkgs["cesium"]["version"] == "1.147.0" and pkgs["satellite.js"]["version"] == "7.1.0"
    for p in pkgs.values():
        assert p["tarball"] == f"https://registry.npmjs.org/{p['name']}/-/{p['name']}-{p['version']}.tgz"
        assert p["integrity"].startswith("sha512-") and len(base64.b64decode(p["integrity"][7:])) == 64
        assert p["version"] in p["dest"]
    # D-029: the JavaScript engine only; no WebAssembly from satellite.js until roadmap 3.11
    assert not [f for f in pkgs["satellite.js"]["files"] if "wasm" in f]


def test_manifest_json_is_sorted_and_stable(tmp_path):
    data = tarball(FILES)
    lock, out = write_lock(tmp_path, data), tmp_path / "out"
    fetch.build(lock, out, None, fetch=lambda url: data)
    doc = json.loads((out / "manifest.json").read_text())
    assert doc["schema"] == 1 and doc["packages"][0]["integrity"] == integrity(data)


# ---- patches (D-041 option B) -------------------------------------------------------------------------------------

def test_a_patch_is_applied_once_and_recorded(tmp_path):
    files = {**FILES, "Build/Cesium/index.js": b'var g=(0,eval)("this");export const a = 1;\n' * 1}
    data = tarball(files)
    lock, out = write_lock(tmp_path, data, patch=PATCH), tmp_path / "out"
    manifest = fetch.build(lock, out, None, fetch=lambda url: data)
    body = (out / "cesium-1.0.0" / "index.js").read_bytes()
    assert body == b"var g=globalThis;export const a = 1;\n"
    (patch,) = manifest["packages"][0]["patches"]
    assert patch["file"] == "cesium-1.0.0/index.js" and patch["replace"] == "globalThis"
    assert patch["sha256_after"] == hashlib.sha256(body).hexdigest() == manifest["files"]["cesium-1.0.0/index.js"]["sha256"]
    assert patch["sha256_before"] == hashlib.sha256(files["Build/Cesium/index.js"]).hexdigest()
    assert fetch.verify(out, fetch.read_lock(lock)[1]) is None


@pytest.mark.parametrize("index_js", [b"export const a = 1;", b'(0,eval)("this");(0,eval)("this");'])
def test_a_patch_that_does_not_match_exactly_once_fails_the_build(tmp_path, index_js):
    data = tarball({**FILES, "Build/Cesium/index.js": index_js})
    lock, out = write_lock(tmp_path, data, patch=PATCH), tmp_path / "out"
    with pytest.raises(fetch.VendorError, match="exactly once"):
        fetch.build(lock, out, None, fetch=lambda url: data)
    assert not out.exists() and not (tmp_path / "out.tmp").exists()


def test_a_patch_needs_file_find_and_replace(tmp_path):
    data = tarball(FILES)
    lock = write_lock(tmp_path, data, patch='\n[[package.patch]]\nfile = "index.js"\nfind = "x"\n')
    with pytest.raises(fetch.VendorError, match="file, find and replace"):
        fetch.read_lock(lock)


def test_committed_lock_patches_cesiums_one_eval():
    lock, _ = fetch.read_lock()
    pkgs = {p["name"]: p for p in lock["package"]}
    assert pkgs["cesium"]["patch"] == [{"file": "index.js", "find": '(0,eval)("this")', "replace": "globalThis"}]
    assert "patch" not in pkgs["satellite.js"]

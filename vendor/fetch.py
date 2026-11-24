"""Fetch, verify and extract the self-hosted viewer packages pinned in vendor/cesium.lock (decision D-014).

    python vendor/fetch.py [--cache DIR] [--out DIR]     download (or reuse the cache), verify, extract, write manifest
    python vendor/fetch.py --check [--out DIR]           verify the extracted files against the manifest; no network

Run by the Heroku build (bin/post_compile), CI's Heroku-identical build and the browser tests. For each package in the
lock it gets the npm tarball (from --cache when a copy there still matches its hash), checks the tarball's sha512
against the lock's `integrity`, extracts only the files the lock lists into <out>/<dest>/, writes pre-compressed
Brotli and gzip copies of text files (the app serves those, like the data files: D-012) and records every file's
SHA-256 in <out>/manifest.json. Any mismatch or error exits non-zero, which fails the build: the live release stays.

The output is rebuilt in a temporary folder and swapped in at the end, so a failed run never leaves half a vendor
folder. When the manifest already matches the lock and every file verifies, nothing is downloaded.

Standard library plus `brotli` (an app dependency). No credentials; the only host contacted is the npm registry.
"""
import argparse
import base64
import gzip
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK = REPO_ROOT / "vendor" / "cesium.lock"
OUT = REPO_ROOT / "static" / "vendor"
MANIFEST = "manifest.json"
ALLOWED_HOSTS = {"registry.npmjs.org"}
COMPRESS = {".js", ".css", ".json", ".md"}   # text files served pre-compressed (images are already compressed)
MAX_TARBALL = 100_000_000                    # bytes: refuse anything absurdly large (Cesium 1.147.0 is 23.4 MB)


class VendorError(Exception):
    """Anything that must fail the build."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_lock(path=LOCK):
    raw = Path(path).read_bytes()
    lock = tomllib.loads(raw.decode("utf-8"))
    if lock.get("schema") != 1:
        raise VendorError(f"{path}: unknown schema {lock.get('schema')!r}")
    for pkg in lock.get("package", []):
        for key in ("name", "version", "tarball", "integrity", "dest", "files"):
            if not pkg.get(key) and key != "strip":
                raise VendorError(f"{path}: package {pkg.get('name')!r} has no {key}")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", pkg["dest"]) or pkg["version"] not in pkg["dest"]:
            raise VendorError(f"{path}: dest {pkg['dest']!r} must be one folder name that includes the version")
        for patch in pkg.get("patch", []):
            if set(patch) != {"file", "find", "replace"} or not patch["file"] or not patch["find"]:
                raise VendorError(f"{path}: package {pkg['name']!r}: a patch needs exactly file, find and replace")
    return lock, sha256(raw)


def check_integrity(data, integrity):
    """npm's Subresource-Integrity style 'sha512-<base64>'."""
    algo, _, expected = integrity.partition("-")
    if algo != "sha512":
        raise VendorError(f"unsupported integrity algorithm {algo!r} (expected sha512)")
    got = base64.b64encode(hashlib.sha512(data).digest()).decode()
    if got != expected:
        raise VendorError(f"integrity mismatch: expected sha512-{expected}, got sha512-{got}")


def download(url):
    host = urllib.parse.urlparse(url).hostname
    if urllib.parse.urlparse(url).scheme != "https" or host not in ALLOWED_HOSTS:
        raise VendorError(f"refusing to download from {url}: only https://{'|'.join(sorted(ALLOWED_HOSTS))}")
    req = urllib.request.Request(url, headers={"User-Agent": "sattrack-vendor-fetch"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read(MAX_TARBALL + 1)
    if len(data) > MAX_TARBALL:
        raise VendorError(f"{url} is larger than {MAX_TARBALL} bytes")
    return data


def get_tarball(pkg, cache_dir, fetch=download):
    """The package's tarball bytes, verified. A cached copy is used only if it still matches the lock."""
    cached = Path(cache_dir) / f"{pkg['name']}-{pkg['version']}.tgz" if cache_dir else None
    if cached and cached.is_file():
        data = cached.read_bytes()
        try:
            check_integrity(data, pkg["integrity"])
            print(f"  {pkg['name']} {pkg['version']}: cached tarball verified")
            return data
        except VendorError:
            print(f"  {pkg['name']} {pkg['version']}: cached tarball does not match the lock; downloading again")
            cached.unlink()
    data = fetch(pkg["tarball"])
    check_integrity(data, pkg["integrity"])
    print(f"  {pkg['name']} {pkg['version']}: downloaded {len(data):,} bytes, sha512 verified")
    if cached:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(data)
    return data


def glob_regex(pattern):
    """'*' within one folder, '**' across folders, everything else literal."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def safe_relative(name):
    parts = name.split("/")
    if name.startswith("/") or "\\" in name or any(p in ("", ".", "..") for p in parts):
        raise VendorError(f"unsafe path in tarball: {name!r}")
    return name


def extract(pkg, data):
    """{relative output path: bytes} for the files the lock lists. Every pattern must match at least one file."""
    patterns = [(p, glob_regex(p)) for p in pkg["files"]]
    used = {p: 0 for p, _ in patterns}
    strip = pkg.get("strip", "")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar:
            if not member.name.startswith("package/"):
                continue
            rel = member.name[len("package/"):]
            hits = [p for p, rx in patterns if rx.match(rel)]
            if not hits:
                continue
            if not member.isfile():   # symlinks, devices, folders: never written
                raise VendorError(f"{pkg['name']}: {rel} is not a regular file")
            safe_relative(rel)
            for p in hits:
                used[p] += 1
            out = rel[len(strip):] if strip and rel.startswith(strip) else rel
            files[f"{pkg['dest']}/{safe_relative(out)}"] = tar.extractfile(member).read()
    unused = [p for p, n in used.items() if n == 0]
    if unused:
        raise VendorError(f"{pkg['name']} {pkg['version']}: no files match {unused}")
    return files


def apply_patches(pkg, files):
    """Apply the lock's patches for this package (D-041) to the extracted {path: bytes}; each `find` must occur
    exactly once in its file. Returns what the manifest records about them."""
    applied = []
    for patch in pkg.get("patch", []):
        rel = f"{pkg['dest']}/{safe_relative(patch['file'])}"
        if rel not in files:
            raise VendorError(f"{pkg['name']}: patch target {patch['file']} is not among the extracted files")
        body, find = files[rel], patch["find"].encode("utf-8")
        found = body.count(find)
        if found != 1:
            raise VendorError(f"{pkg['name']} {pkg['version']}: patch for {patch['file']} expects {patch['find']!r} "
                              f"exactly once, found it {found} times: review the patch for this version")
        files[rel] = body.replace(find, patch["replace"].encode("utf-8"))
        applied.append({"file": rel, "find": patch["find"], "replace": patch["replace"],
                        "sha256_before": sha256(body), "sha256_after": sha256(files[rel])})
    return applied


def variants(rel, body):
    """Pre-compressed copies worth keeping: {'br': bytes, 'gzip': bytes} for text files that shrink."""
    if Path(rel).suffix not in COMPRESS:
        return {}
    import brotli   # an app dependency (pyproject.toml); imported here so --check needs only the standard library
    out = {"br": brotli.compress(body, quality=11), "gzip": gzip.compress(body, compresslevel=9, mtime=0)}
    return {enc: b for enc, b in out.items() if len(b) < 0.9 * len(body)}


SUFFIX = {"br": ".br", "gzip": ".gz"}


def verify(out_dir, lock_sha):
    """None if <out_dir> matches its manifest and the manifest matches the lock, else the reason."""
    out_dir = Path(out_dir)
    try:
        manifest = json.loads((out_dir / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return f"no readable manifest ({type(e).__name__})"
    if manifest.get("lock_sha256") != lock_sha:
        return "the manifest was written for a different vendor/cesium.lock"
    for rel, entry in manifest["files"].items():
        for enc, info in [("identity", entry)] + list(entry.get("encodings", {}).items()):
            path = out_dir / (rel + SUFFIX.get(enc, ""))
            try:
                if sha256(path.read_bytes()) != info["sha256"]:
                    return f"{path.relative_to(out_dir)}: SHA-256 differs from the manifest"
            except OSError:
                return f"{path.relative_to(out_dir)}: missing"
    return None


def _rename(src, dst, attempts=20):
    """Rename a folder, retrying briefly: on a developer's Windows machine a sync client or virus scanner can hold
    freshly written files for a moment (PermissionError). On Linux builds the first attempt succeeds."""
    import time
    for i in range(attempts):
        try:
            return src.rename(dst)
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(0.5)


def build(lock_path=LOCK, out_dir=OUT, cache_dir=None, fetch=download):
    lock, lock_sha = read_lock(lock_path)
    out_dir = Path(out_dir)
    if verify(out_dir, lock_sha) is None:
        print(f"vendor: {out_dir} already matches {Path(lock_path).name}; nothing to do")
        return json.loads((out_dir / MANIFEST).read_text(encoding="utf-8"))
    print(f"vendor: building {out_dir} from {Path(lock_path).name}")
    tmp = out_dir.with_name(out_dir.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    manifest = {"schema": 1, "lock_sha256": lock_sha, "packages": [], "files": {}}
    try:
        for pkg in lock["package"]:
            files = extract(pkg, get_tarball(pkg, cache_dir, fetch))
            patches = apply_patches(pkg, files)
            manifest["packages"].append({**{k: pkg[k] for k in ("name", "version", "integrity", "licence", "dest")
                                            if k in pkg}, **({"patches": patches} if patches else {})})
            for rel, body in sorted(files.items()):
                path = tmp / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                entry = {"sha256": sha256(body), "bytes": len(body), "encodings": {}}
                for enc, comp in variants(rel, body).items():
                    (tmp / (rel + SUFFIX[enc])).write_bytes(comp)
                    entry["encodings"][enc] = {"sha256": sha256(comp), "bytes": len(comp)}
                manifest["files"][rel] = entry
            print(f"  {pkg['name']} {pkg['version']}: {len(files)} files, "
                  f"{sum(len(b) for b in files.values()) / 1e6:.2f} MB -> {pkg['dest']}/"
                  + (f", {len(patches)} patch(es) applied" if patches else ""))
        manifest["total_bytes"] = sum(e["bytes"] + sum(v["bytes"] for v in e["encodings"].values())
                                      for e in manifest["files"].values())
        (tmp / MANIFEST).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        problem = verify(tmp, lock_sha)
        if problem:
            raise VendorError(f"fresh build does not verify: {problem}")
        old = out_dir.with_name(out_dir.name + ".old")
        shutil.rmtree(old, ignore_errors=True)
        if out_dir.exists():
            _rename(out_dir, old)
        try:
            _rename(tmp, out_dir)
        except OSError:
            if old.exists() and not out_dir.exists():
                _rename(old, out_dir)   # put the previous files back
            raise
        shutil.rmtree(old, ignore_errors=True)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    print(f"vendor: {len(manifest['files'])} files, {manifest['total_bytes'] / 1e6:.2f} MB on disk "
          f"(with pre-compressed copies)")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", help="folder to keep verified tarballs between builds")
    ap.add_argument("--out", default=str(OUT), help="output folder (default static/vendor)")
    ap.add_argument("--lock", default=str(LOCK))
    ap.add_argument("--check", action="store_true", help="verify the output against the manifest and exit")
    args = ap.parse_args(argv)
    try:
        if args.check:
            problem = verify(args.out, read_lock(args.lock)[1])
            if problem:
                raise VendorError(problem)
            print(f"vendor: {args.out} verified")
        else:
            build(args.lock, args.out, args.cache)
    except (VendorError, OSError, tarfile.TarError, ValueError) as e:
        print(f"vendor: FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Manajemen runtime GE-Proton: scan lokal, daftar rilis GitHub, download."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import config
from .models import Runtime

RELEASES_API = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases"
_TARBALL_SUFFIXES = (".tar.gz", ".tar.xz")
_CHECKSUM_SUFFIXES = (".sha512sum", ".sha256sum")


def is_runtime_dir(path: Path) -> bool:
    return (Path(path) / "proton").exists()


def natural_key(name: str) -> tuple:
    parts = re.split(r"(\d+)", name)
    return tuple(int(p) if p.isdigit() else p for p in parts)


def _scan_dir(base: Path, source: str) -> list[Runtime]:
    if not base.exists():
        return []
    out = []
    for child in base.iterdir():
        if child.is_dir() and is_runtime_dir(child):
            out.append(Runtime(name=child.name, path=str(child), source=source))
    return out


def scan_runtimes() -> list[Runtime]:
    found: dict[str, Runtime] = {}
    for rt in _scan_dir(config.runtimes_dir(), "managed"):
        found.setdefault(rt.name, rt)
    for extra in config.load_config().get("extra_runtime_dirs", []):
        for rt in _scan_dir(Path(extra), "local"):
            found.setdefault(rt.name, rt)
    return sorted(found.values(), key=lambda r: natural_key(r.name), reverse=True)


@dataclass(frozen=True)
class Release:
    tag: str
    tarball_url: str
    checksum_url: str | None


def parse_releases(payload: list[dict]) -> list["Release"]:
    out = []
    for rel in payload:
        tarball = checksum = None
        for asset in rel.get("assets", []):
            name = asset.get("name", "")
            url = asset.get("browser_download_url")
            if name.endswith(_TARBALL_SUFFIXES):
                tarball = url
            elif name.endswith(_CHECKSUM_SUFFIXES):
                checksum = url
        if tarball:
            out.append(Release(tag=rel.get("tag_name", ""),
                               tarball_url=tarball, checksum_url=checksum))
    return out


def fetch_releases(limit: int = 20, opener=urllib.request.urlopen) -> list["Release"]:
    req = urllib.request.Request(RELEASES_API,
                                 headers={"Accept": "application/vnd.github+json"})
    target = req if opener is urllib.request.urlopen else RELEASES_API
    with opener(target, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    if not isinstance(payload, list):
        # GitHub mengembalikan objek error (mis. rate limit), bukan daftar rilis.
        msg = payload.get("message", "respons tidak dikenal") \
            if isinstance(payload, dict) else "respons tidak dikenal"
        raise RuntimeError(f"GitHub API: {msg}")
    return parse_releases(payload)[:limit]


def verify_sha512(file_path: Path, checksum_text: str,
                  asset_name: str = "") -> bool:
    lines = [ln.split() for ln in checksum_text.strip().splitlines() if ln.split()]
    expected = ""
    if asset_name:
        # File checksum bisa berisi beberapa baris; cocokkan dengan nama aset.
        for parts in lines:
            if len(parts) >= 2 and parts[-1].lstrip("*") == asset_name:
                expected = parts[0].lower()
                break
    if not expected and lines:
        expected = lines[0][0].lower()
    if not expected:
        return False
    h = hashlib.sha512()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected


def _is_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def extract_tarball(tarball_path: Path, dest_dir: Path) -> Path:
    """Ekstrak ke staging tersembunyi lalu pindahkan secara atomik.

    Kegagalan di tengah ekstraksi (disk penuh, arsip terpotong, proses mati)
    tidak boleh meninggalkan folder runtime setengah jadi di `dest_dir` yang
    kemudian lolos `is_runtime_dir()` dan dianggap terpasang.
    """
    dest_dir = Path(dest_dir)
    staging = Path(tempfile.mkdtemp(dir=dest_dir, prefix=".extract-"))
    try:
        with tarfile.open(tarball_path) as tar:
            members = tar.getmembers()
            top_levels = {m.name.split("/", 1)[0] for m in members if m.name}
            for m in members:
                if not _is_within(staging, staging / m.name):
                    raise RuntimeError(f"Entri tar tidak aman: {m.name}")
            # Filter "data" juga menolak symlink/hardlink yang menunjuk
            # keluar arsip serta device node.
            tar.extractall(staging, filter="data")
        if len(top_levels) != 1:
            raise RuntimeError("Arsip runtime tidak memiliki satu folder root")
        top = top_levels.pop()
        final = dest_dir / top
        if final.exists():
            shutil.rmtree(final)
        os.replace(staging / top, final)
        return final
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _download_to(url: str, dest: Path, opener, progress=None) -> None:
    with opener(url, timeout=60) as resp:
        total = 0
        headers = getattr(resp, "headers", None)
        if headers is not None:
            try:
                total = int(headers.get("Content-Length", 0))
            except (TypeError, ValueError):
                total = 0
        done = 0
        with open(dest, "wb") as out:
            for chunk in iter(lambda: resp.read(1 << 20), b""):
                out.write(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)


# Dua thread (Runtime Manager + launch "Automatic") tidak boleh mengunduh/
# mengekstrak rilis yang sama secara bersamaan.
_DOWNLOAD_LOCK = threading.Lock()


def download_runtime(release: "Release", progress=None,
                     opener=urllib.request.urlopen) -> Runtime:
    with _DOWNLOAD_LOCK:
        rt_dir = config.runtimes_dir()
        existing = rt_dir / release.tag if release.tag else None
        if existing is not None and is_runtime_dir(existing):
            # Sudah diunduh thread lain selagi kita menunggu lock.
            return Runtime(name=existing.name, path=str(existing),
                           source="managed")
        fd, tmp_name = tempfile.mkstemp(dir=rt_dir, suffix=".tar.gz")
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            _download_to(release.tarball_url, tmp, opener, progress)
            if release.checksum_url:
                with opener(release.checksum_url, timeout=30) as resp:
                    checksum_text = resp.read().decode()
                asset = release.tarball_url.rsplit("/", 1)[-1]
                if not verify_sha512(tmp, checksum_text, asset_name=asset):
                    raise RuntimeError(f"Checksum gagal untuk {release.tag}")
            folder = extract_tarball(tmp, rt_dir)
        finally:
            if tmp.exists():
                tmp.unlink()
    return Runtime(name=folder.name, path=str(folder), source="managed")


def newest_installed() -> Runtime | None:
    rts = scan_runtimes()
    return rts[0] if rts else None


def ensure_runtime(name: str = "", progress=None, on_status=None) -> Runtime:
    """Kembalikan runtime yang siap pakai.

    - Jika `name` diberikan & sudah terpasang -> pakai itu.
    - Jika `name` kosong & ada runtime terpasang -> pakai yang terbaru.
    - Jika belum ada yang cocok -> unduh (tag `name` bila ada di rilis, else terbaru).
    """
    installed = scan_runtimes()
    if name:
        for rt in installed:
            if rt.name == name:
                return rt
    elif installed:
        return installed[0]

    if on_status:
        on_status("Mengunduh GE-Proton…")
    rels = fetch_releases(limit=30)
    rel = next((r for r in rels if r.tag == name), None) if name else None
    if rel is None:
        rel = rels[0] if rels else None
    if rel is None:
        raise RuntimeError("Gagal mengambil daftar rilis GE-Proton")
    if on_status:
        on_status(f"Mengunduh {rel.tag}…")
    return download_runtime(rel, progress=progress)

"""Unduh & pasang Microsoft Edge WebView2 Runtime ke sebuah prefix.

Banyak aplikasi (mis. Clip Studio Paint) menampilkan UI berbasis web lewat
WebView2; tanpa runtime ini panel-panelnya tampil putih kosong. Bootstrapper
resmi Microsoft berukuran kecil (~2 MB), memilih arsitektur secara otomatis,
dan mengunduh runtime dari dalam prefix (umu-run punya akses jaringan).
"""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path

from . import config

# Link permanen resmi Microsoft untuk Evergreen Bootstrapper.
BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
INSTALL_ARGS = ["/silent", "/install"]


def installer_path(on_status=None, opener=urllib.request.urlopen) -> Path:
    """Kembalikan path installer WebView2, unduh bila belum ada.

    Bisa di-override dengan env `AGUSEMU_WEBVIEW2_INSTALLER` untuk memakai
    Standalone Installer yang sudah diunduh manual (lebih andal offline).
    """
    override = os.environ.get("AGUSEMU_WEBVIEW2_INSTALLER")
    if override and Path(override).is_file():
        return Path(override)
    dest_dir = config.data_dir() / "tools"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "MicrosoftEdgeWebview2Setup.exe"
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    if on_status:
        on_status("Mengunduh WebView2 installer…")
    tmp = dest.with_name(dest.name + ".tmp")
    req = urllib.request.Request(BOOTSTRAPPER_URL,
                                 headers={"User-Agent": "AgusEmu"})
    target = req if opener is urllib.request.urlopen else BOOTSTRAPPER_URL
    with opener(target, timeout=120) as resp:
        tmp.write_bytes(resp.read())
    os.replace(tmp, dest)
    return dest

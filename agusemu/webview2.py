"""Unduh & pasang Microsoft Edge WebView2 Runtime ke sebuah prefix.

Banyak aplikasi (mis. Clip Studio Paint) menampilkan UI berbasis web lewat
WebView2; tanpa runtime ini panel-panelnya tampil putih kosong. Bootstrapper
resmi Microsoft berukuran kecil (~2 MB), memilih arsitektur secara otomatis,
dan mengunduh runtime dari dalam prefix (umu-run punya akses jaringan).
"""
from __future__ import annotations

import os
import subprocess
import threading
import urllib.request
from pathlib import Path

from . import config
from .models import App, Runtime

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


def is_installed(prefix: str) -> bool:
    """True jika runtime WebView2 (msedgewebview2.exe) sudah ada di prefix."""
    root = Path(prefix)
    if not root.exists():
        return False
    pattern = "EdgeWebView/Application/*/msedgewebview2.exe"
    return any(root.glob(f"**/{pattern}"))


def install(app: App, runtime: Runtime, on_output=None,
            popen=subprocess.Popen, sleep=None, timeout: int = 300) -> int:
    """Pasang WebView2 ke prefix `app`, lalu tutup sesi Wine agar selesai.

    Installer resmi meninggalkan proses updater yang membuat prefix tetap
    hidup, sehingga Proton `waitforexitandrun` tak pernah kembali (command
    tampak menggantung). Kita pantau sampai runtime terdeteksi lalu matikan
    sesi Wine-nya secara paksa.
    """
    from . import deps, launcher
    if sleep is None:
        import time
        sleep = time.sleep

    if is_installed(app.prefix):
        if on_output:
            on_output("WebView2 sudah terpasang di prefix ini.")
        return 0

    installer = installer_path(on_status=on_output)
    if on_output:
        on_output("Menjalankan installer WebView2 (silent)…")
    umu = deps.require_umu_run()
    env = launcher.build_env(app, runtime)
    cmd = [umu, str(installer), *INSTALL_ARGS]
    proc = popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                 encoding="utf-8", errors="replace", bufsize=1,
                 start_new_session=True)

    reader = threading.Thread(target=launcher.stream_and_wait,
                              args=(proc, on_output), daemon=True)
    reader.start()

    waited = 0
    while reader.is_alive():
        if is_installed(app.prefix):
            if on_output:
                on_output("[WebView2 terpasang — menutup sesi installer…]")
            launcher.shutdown_prefix(app.prefix, runtime)
            break
        if waited >= timeout:
            if on_output:
                on_output("[timeout menunggu WebView2 — menutup sesi…]")
            launcher.shutdown_prefix(app.prefix, runtime)
            break
        sleep(2)
        waited += 2

    reader.join(timeout=30)
    return 0 if is_installed(app.prefix) else 1

"""Resolusi dependensi eksternal (umu-run, winetricks)."""
from __future__ import annotations

import os
import shutil
import urllib.request
from pathlib import Path

INSTALL_HINT = (
    "umu-run not found. Install umu-launcher: download 'umu-run' from "
    "https://github.com/Open-Wine-Components/umu-launcher/releases and put "
    "it on PATH, or set the AGUSEMU_UMU_RUN env var to its path."
)

WINETRICKS_URL = ("https://raw.githubusercontent.com/Winetricks/winetricks/"
                  "master/src/winetricks")


def _is_exec(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _bundled_umu() -> str | None:
    candidate = Path(__file__).resolve().parent.parent / "bundle" / "umu-run"
    return str(candidate) if _is_exec(candidate) else None


def find_umu_run() -> str | None:
    env = os.environ.get("AGUSEMU_UMU_RUN")
    if env and _is_exec(Path(env)):
        return env
    found = shutil.which("umu-run")
    if found:
        return found
    return _bundled_umu()


def require_umu_run() -> str:
    path = find_umu_run()
    if not path:
        raise FileNotFoundError(INSTALL_HINT)
    return path


def _managed_winetricks() -> Path:
    from . import config
    return config.data_dir() / "tools" / "winetricks"


def find_winetricks() -> str | None:
    env = os.environ.get("AGUSEMU_WINETRICKS")
    if env and _is_exec(Path(env)):
        return env
    found = shutil.which("winetricks")
    if found:
        return found
    managed = _managed_winetricks()
    return str(managed) if _is_exec(managed) else None


def ensure_winetricks(on_status=None,
                      opener=urllib.request.urlopen) -> str:
    """Kembalikan path winetricks; unduh salinan terkelola bila tidak ada.

    winetricks hanyalah satu shell script, jadi pengguna AppImage/sistem
    tanpa paket winetricks tetap bisa memakai fitur komponen.
    """
    found = find_winetricks()
    if found:
        return found
    dest = _managed_winetricks()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if on_status:
        on_status("Mengunduh winetricks…")
    tmp = dest.with_name(dest.name + ".tmp")
    with opener(WINETRICKS_URL, timeout=60) as resp:
        tmp.write_bytes(resp.read())
    tmp.chmod(0o755)
    os.replace(tmp, dest)
    return str(dest)

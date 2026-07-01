"""Resolusi dependensi eksternal (umu-run, winetricks)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

INSTALL_HINT = (
    "umu-run tidak ditemukan. Pasang umu-launcher: unduh 'umu-run' dari "
    "https://github.com/Open-Wine-Components/umu-launcher/releases lalu "
    "letakkan di PATH, atau set env AGUSEMU_UMU_RUN ke path-nya."
)


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


def find_winetricks() -> str | None:
    env = os.environ.get("AGUSEMU_WINETRICKS")
    if env and _is_exec(Path(env)):
        return env
    return shutil.which("winetricks")

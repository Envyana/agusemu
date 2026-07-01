"""Membuat shortcut .desktop untuk aplikasi di library."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from . import config
from .models import App


def desktop_entry_text(app: App, exec_cmd: str, icon_path: str) -> str:
    return "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        f"Name={app.name}",
        f"Exec={exec_cmd}",
        f"Icon={icon_path}",
        "Terminal=false",
        "Categories=Game;Utility;",
        f"X-AgusEmu-Id={app.id}",
        "",
    ])


def applications_dir() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg) if xdg else Path.home() / ".local" / "share"
    d = root / "applications"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_shortcut(app: App, launch_exec: str, icon_src: str | None = None) -> Path:
    icon_path = ""
    if icon_src and Path(icon_src).exists():
        icons = config.data_dir() / "icons"
        icons.mkdir(parents=True, exist_ok=True)
        dest = icons / f"{app.id}.png"
        shutil.copyfile(icon_src, dest)
        icon_path = str(dest)
    path = applications_dir() / f"agusemu-{app.id}.desktop"
    path.write_text(desktop_entry_text(app, launch_exec, icon_path))
    path.chmod(0o755)
    return path

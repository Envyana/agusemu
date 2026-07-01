"""Desktop integration for the AppImage (best-effort; never crashes startup).

Installs a .desktop launcher + icon so the AE logo shows in the app grid, and
sets a custom icon on the AppImage file itself. The icon is stored in the
AgusEmu data dir (always writable) instead of the shared hicolor theme dir,
which may be root-owned/unwritable on some systems.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from . import config

APP_ID = "com.patopo.AgusEmu"


def _data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg) if xdg else Path.home() / ".local" / "share"


def _desktop_text(exec_cmd: str, icon_path: str) -> str:
    return "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        "Name=AgusEmu",
        "Comment=Run Windows apps and games via GE-Proton",
        f"Exec={exec_cmd}",
        f"Icon={icon_path}",
        "Terminal=false",
        "Categories=Game;Utility;",
        "",
    ])


def _do_integrate(appimage: str, logo_path: str | Path) -> None:
    # Store icon in a writable location (data dir), reference it by absolute path.
    icon = Path(logo_path)
    try:
        dest = config.data_dir() / "agusemu.png"
        shutil.copyfile(str(logo_path), dest)
        icon = dest
    except OSError:
        pass

    try:
        apps = _data_home() / "applications"
        apps.mkdir(parents=True, exist_ok=True)
        (apps / f"{APP_ID}.desktop").write_text(
            _desktop_text(f'"{appimage}"', str(icon)))
    except OSError:
        apps = None

    cmds = []
    if apps is not None:
        cmds.append(["update-desktop-database", str(apps)])
    if icon.exists():
        cmds.append(["gio", "set", appimage,
                     "metadata::custom-icon", icon.as_uri()])
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
        except (OSError, subprocess.SubprocessError):
            pass


def integrate_appimage(logo_path: str | Path) -> bool:
    """Install launcher + icon for the running AppImage. Never raises."""
    appimage = os.environ.get("APPIMAGE")
    if not appimage:
        return False
    try:
        _do_integrate(appimage, logo_path)
        return True
    except Exception:
        return False

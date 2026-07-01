"""Desktop integration: install a .desktop launcher + icon when run as AppImage.

This makes the AE logo show up in the GNOME app grid and (best effort) as the
AppImage file icon in the file manager.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

APP_ID = "com.patopo.AgusEmu"


def _data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg) if xdg else Path.home() / ".local" / "share"


def _desktop_text(exec_cmd: str) -> str:
    return "\n".join([
        "[Desktop Entry]",
        "Type=Application",
        "Name=AgusEmu",
        "Comment=Run Windows apps and games via GE-Proton",
        f"Exec={exec_cmd}",
        f"Icon={APP_ID}",
        "Terminal=false",
        "Categories=Game;Utility;",
        "",
    ])


def integrate_appimage(logo_path: str | Path) -> bool:
    """Install launcher + icon for the running AppImage. No-op if not an AppImage."""
    appimage = os.environ.get("APPIMAGE")
    if not appimage:
        return False
    dh = _data_home()
    icon_dir = dh / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon_dest = icon_dir / f"{APP_ID}.png"
    try:
        shutil.copyfile(str(logo_path), icon_dest)
    except OSError:
        pass

    apps = dh / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / f"{APP_ID}.desktop").write_text(_desktop_text(f'"{appimage}"'))

    for cmd in (["update-desktop-database", str(apps)],
                ["gtk-update-icon-cache", "-f", str(dh / "icons" / "hicolor")],
                ["gio", "set", appimage, "metadata::custom-icon", icon_dest.as_uri()]):
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
        except (OSError, subprocess.SubprocessError):
            pass
    return True

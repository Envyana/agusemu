"""Desktop integration: install a .desktop launcher + icon when run as AppImage.

Best-effort only: this makes the AE logo appear in the GNOME app grid and (best
effort) as the AppImage file icon. It must NEVER prevent the app from starting,
so every failure is swallowed.
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


def _do_integrate(appimage: str, logo_path: str | Path) -> None:
    dh = _data_home()
    icon_dir = dh / "icons" / "hicolor" / "256x256" / "apps"
    icon_dest = icon_dir / f"{APP_ID}.png"
    try:
        icon_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(logo_path), icon_dest)
    except OSError:
        pass  # e.g. icon dir not writable; skip icon, keep going

    try:
        apps = dh / "applications"
        apps.mkdir(parents=True, exist_ok=True)
        (apps / f"{APP_ID}.desktop").write_text(_desktop_text(f'"{appimage}"'))
    except OSError:
        pass

    for cmd in (["update-desktop-database", str(dh / "applications")],
                ["gtk-update-icon-cache", "-f", str(dh / "icons" / "hicolor")],
                ["gio", "set", appimage, "metadata::custom-icon", icon_dest.as_uri()]):
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

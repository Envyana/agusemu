"""Penyimpanan library aplikasi (library.json)."""
from __future__ import annotations

import threading

from . import config
from .models import App

# Launch/install berjalan di worker thread dan ikut menulis library, jadi
# seluruh siklus load-modify-write harus diserialisasi.
_LOCK = threading.RLock()


def load_apps() -> list[App]:
    data = config.load_json_safe(config.library_path(), {})
    if not isinstance(data, dict):
        return []
    entries = data.get("apps", [])
    if not isinstance(entries, list):
        return []
    apps = []
    for d in entries:
        if not isinstance(d, dict):
            continue
        try:
            apps.append(App.from_dict(d))
        except (TypeError, ValueError):
            # Satu entri cacat tidak boleh menggagalkan seluruh library.
            continue
    return apps


def save_apps(apps: list[App]) -> None:
    payload = {"apps": [a.to_dict() for a in apps]}
    with _LOCK:
        config.atomic_write_json(config.library_path(), payload)


def get_app(app_id: str) -> App | None:
    for a in load_apps():
        if a.id == app_id:
            return a
    return None


def add_app(app: App) -> None:
    with _LOCK:
        apps = load_apps()
        if any(a.id == app.id for a in apps):
            raise ValueError(f"App id sudah ada: {app.id}")
        save_apps([*apps, app])


def update_app(app: App) -> None:
    with _LOCK:
        apps = load_apps()
        if not any(a.id == app.id for a in apps):
            raise KeyError(app.id)
        save_apps([app if a.id == app.id else a for a in apps])


def set_runtime(app_id: str, runtime: str) -> None:
    """Perbarui hanya field runtime dari rekaman TERKINI di disk.

    Dipakai worker launch setelah unduhan runtime selesai; tidak menimpa
    editan lain yang terjadi selama unduhan, dan tidak apa-apa jika app
    sudah dihapus.
    """
    with _LOCK:
        apps = load_apps()
        current = next((a for a in apps if a.id == app_id), None)
        if current is None or current.runtime == runtime:
            return
        save_apps([a.with_changes(runtime=runtime) if a.id == app_id else a
                   for a in apps])


def remove_app(app_id: str) -> None:
    with _LOCK:
        save_apps([a for a in load_apps() if a.id != app_id])

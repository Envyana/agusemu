"""Penyimpanan library aplikasi (library.json)."""
from __future__ import annotations

import json

from . import config
from .models import App


def load_apps() -> list[App]:
    path = config.library_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [App.from_dict(d) for d in data.get("apps", [])]


def save_apps(apps: list[App]) -> None:
    payload = {"apps": [a.to_dict() for a in apps]}
    config.library_path().write_text(json.dumps(payload, indent=2))


def get_app(app_id: str) -> App | None:
    for a in load_apps():
        if a.id == app_id:
            return a
    return None


def add_app(app: App) -> None:
    apps = load_apps()
    if any(a.id == app.id for a in apps):
        raise ValueError(f"App id sudah ada: {app.id}")
    save_apps([*apps, app])


def update_app(app: App) -> None:
    apps = load_apps()
    if not any(a.id == app.id for a in apps):
        raise KeyError(app.id)
    save_apps([app if a.id == app.id else a for a in apps])


def remove_app(app_id: str) -> None:
    save_apps([a for a in load_apps() if a.id != app_id])

"""Path XDG dan setting global untuk AgusEmu."""
from __future__ import annotations

import json
import os
from pathlib import Path

APP_DIRNAME = "AgusEmu"
DEFAULT_CONFIG = {"extra_runtime_dirs": [], "default_runtime": None}


def data_dir() -> Path:
    override = os.environ.get("AGUSEMU_DATA_DIR")
    if override:
        base = Path(override)
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        root = Path(xdg) if xdg else Path.home() / ".local" / "share"
        base = root / APP_DIRNAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def runtimes_dir() -> Path:
    d = data_dir() / "runtimes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def prefixes_dir() -> Path:
    d = data_dir() / "prefixes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def icons_dir() -> Path:
    d = data_dir() / "icons"
    d.mkdir(parents=True, exist_ok=True)
    return d


def library_path() -> Path:
    return data_dir() / "library.json"


def config_path() -> Path:
    return data_dir() / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    data = json.loads(path.read_text())
    return {**DEFAULT_CONFIG, **data}


def save_config(cfg: dict) -> None:
    config_path().write_text(json.dumps(cfg, indent=2))

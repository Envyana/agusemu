"""Path XDG dan setting global untuk AgusEmu."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

APP_DIRNAME = "AgusEmu"
DEFAULT_CONFIG = {"extra_runtime_dirs": [], "default_runtime": None}


def atomic_write_json(path: Path, payload) -> None:
    """Tulis JSON secara atomik (temp + fsync + rename) agar crash di tengah
    penulisan tidak pernah meninggalkan file setengah jadi/korup."""
    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name,
                                    suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_json_safe(path: Path, default):
    """Baca JSON; jika file korup, amankan sebagai backup `.corrupt` dan
    kembalikan default alih-alih membuat aplikasi gagal start."""
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        try:
            path.replace(path.with_name(path.name + ".corrupt"))
        except OSError:
            pass
        return default


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
    data = load_json_safe(config_path(), dict(DEFAULT_CONFIG))
    if not isinstance(data, dict):
        data = {}
    cfg = {**DEFAULT_CONFIG, **data}
    # Nilai null/eksplisit yang salah tipe (mis. "extra_runtime_dirs": null)
    # tidak boleh menembus merge dan membuat pemanggil crash.
    if not isinstance(cfg.get("extra_runtime_dirs"), list):
        cfg["extra_runtime_dirs"] = []
    return cfg


def save_config(cfg: dict) -> None:
    atomic_write_json(config_path(), cfg)

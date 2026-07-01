"""Menyusun environment & menjalankan umu-run."""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from . import deps
from .models import App, Runtime


def build_env(app: App, runtime: Runtime, base_env: dict | None = None) -> dict:
    env = dict(os.environ if base_env is None else base_env)
    env["GAMEID"] = "0"
    env["PROTONPATH"] = runtime.path
    env["WINEPREFIX"] = app.prefix
    env["STEAM_COMPAT_DATA_PATH"] = app.prefix
    if not app.dxvk_enabled:
        env["PROTON_USE_WINED3D"] = "1"
    env.update(app.env or {})
    return env


def build_command(app: App, umu_run: str) -> list[str]:
    return [umu_run, app.exe_path, *shlex.split(app.args or "")]


def launch(app: App, runtime: Runtime, on_output=None,
           runner=subprocess.Popen) -> int:
    Path(app.prefix).mkdir(parents=True, exist_ok=True)
    umu_run = deps.require_umu_run()
    cmd = build_command(app, umu_run)
    env = build_env(app, runtime)
    proc = runner(cmd, env=env, stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, text=True, bufsize=1)
    if proc.stdout is not None:
        for line in proc.stdout:
            if on_output:
                on_output(line.rstrip("\n"))
    return proc.wait()

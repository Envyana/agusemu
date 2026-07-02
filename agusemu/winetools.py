"""Operasi prefix: winetricks & winecfg (via umu-run)."""
from __future__ import annotations

import subprocess

from . import deps, launcher
from .models import App, Runtime


def winetricks_command(app: App, runtime: Runtime, verbs: list[str],
                       umu_run: str, winetricks: str) -> tuple[list[str], dict]:
    return [umu_run, winetricks, *verbs], launcher.build_env(app, runtime)


def winecfg_command(app: App, runtime: Runtime, umu_run: str) -> tuple[list[str], dict]:
    return [umu_run, "winecfg"], launcher.build_env(app, runtime)


def _stream(cmd, env, on_output, runner) -> int:
    proc = runner(cmd, env=env, stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, encoding="utf-8",
                  errors="replace", bufsize=1)
    return launcher.stream_and_wait(proc, on_output)


def run_winetricks(app: App, runtime: Runtime, verbs: list[str],
                   on_output=None, runner=subprocess.Popen) -> int:
    umu_run = deps.require_umu_run()
    try:
        winetricks = deps.ensure_winetricks(on_status=on_output)
    except OSError as exc:
        raise FileNotFoundError(
            "winetricks tidak ditemukan di PATH dan gagal diunduh "
            f"({exc}). Pasang winetricks atau periksa koneksi internet.")
    cmd, env = winetricks_command(app, runtime, verbs, umu_run, winetricks)
    return _stream(cmd, env, on_output, runner)


def run_winecfg(app: App, runtime: Runtime,
                on_output=None, runner=subprocess.Popen) -> int:
    umu_run = deps.require_umu_run()
    cmd, env = winecfg_command(app, runtime, umu_run)
    return _stream(cmd, env, on_output, runner)

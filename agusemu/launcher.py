"""Build environment & run umu-run."""
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
    if app.nvapi_enabled:
        # Proton menyembunyikan NVAPI secara default; aplikasi yang membaca
        # GPU NVIDIA (NVAPI/CUDA/PhysX) butuh dxvk-nvapi diaktifkan.
        env["PROTON_ENABLE_NVAPI"] = "1"
        env["DXVK_ENABLE_NVAPI"] = "1"
    env.update(app.env or {})
    return env


def to_wine_path(path: str) -> str:
    """Convert a Linux path to a Wine path (the Z: drive maps to /)."""
    return "Z:" + os.path.abspath(path).replace("/", "\\")


def build_command(app: App, umu_run: str) -> list[str]:
    try:
        extra = shlex.split(app.args or "")
    except ValueError as exc:
        raise ValueError(
            f"Argumen tidak valid ({exc}): {app.args!r}") from exc
    if app.exe_path.lower().endswith(".msi"):
        # Windows installers (.msi) run through msiexec; the .msi argument must
        # be a Wine path (Z:\...), not a Linux path, or msiexec cannot open it.
        return [umu_run, "msiexec", "/i", to_wine_path(app.exe_path), *extra]
    return [umu_run, app.exe_path, *extra]


def stream_and_wait(proc, on_output=None) -> int:
    """Baca stdout proses sampai habis, tutup pipe, lalu reap prosesnya.

    Callback output yang melempar (mis. disk penuh saat menulis log) atau
    error baca pipe tidak boleh menghentikan pembacaan: pipe yang berhenti
    dibaca membuat anak proses macet saat buffernya penuh, dan proses yang
    tidak pernah di-`wait()` menjadi zombie.
    """
    try:
        if proc.stdout is not None:
            for line in proc.stdout:
                if on_output:
                    try:
                        on_output(line.rstrip("\n"))
                    except Exception:
                        pass
    except OSError:
        pass
    finally:
        if proc.stdout is not None:
            try:
                proc.stdout.close()
            except OSError:
                pass
    return proc.wait()


def launch(app: App, runtime: Runtime, on_output=None,
           runner=subprocess.Popen) -> int:
    Path(app.prefix).mkdir(parents=True, exist_ok=True)
    umu_run = deps.require_umu_run()
    cmd = build_command(app, umu_run)
    env = build_env(app, runtime)
    # Output Wine tidak dijamin UTF-8 valid; errors="replace" mencegah
    # UnicodeDecodeError mematikan loop pembacaan di tengah jalan.
    proc = runner(cmd, env=env, stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, encoding="utf-8",
                  errors="replace", bufsize=1)
    return stream_and_wait(proc, on_output)

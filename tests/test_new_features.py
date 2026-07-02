"""Test untuk fitur baru: dukungan NVAPI dan auto-download winetricks."""
import io
import shutil

from agusemu import deps, launcher, winetools
from agusemu.models import App, Runtime


def _app(**kw):
    base = dict(id="a-1", name="A", exe_path="/a.exe",
                runtime="r", prefix="/pfx/a-1")
    base.update(kw)
    return App(**base)


def _rt():
    return Runtime(name="r", path="/rt/r", source="managed")


# --- NVAPI ---

def test_build_env_nvapi_enabled_sets_vars():
    env = launcher.build_env(_app(nvapi_enabled=True), _rt(), base_env={})
    assert env["PROTON_ENABLE_NVAPI"] == "1"
    assert env["DXVK_ENABLE_NVAPI"] == "1"


def test_build_env_nvapi_disabled_by_default():
    env = launcher.build_env(_app(), _rt(), base_env={})
    assert "PROTON_ENABLE_NVAPI" not in env
    assert "DXVK_ENABLE_NVAPI" not in env


def test_app_from_dict_old_payload_defaults_nvapi_false():
    # library.json lama tidak punya field nvapi_enabled.
    d = _app().to_dict()
    d.pop("nvapi_enabled")
    assert App.from_dict(d).nvapi_enabled is False


# --- winetricks auto-download ---

class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AGUSEMU_WINETRICKS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _name: None)


def test_ensure_winetricks_downloads_when_missing(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    calls = []

    def fake_opener(url, timeout=0):
        calls.append(url)
        return Resp(b"#!/bin/sh\necho winetricks\n")

    path = deps.ensure_winetricks(opener=fake_opener)
    assert calls == [deps.WINETRICKS_URL]
    assert path == str(tmp_path / "tools" / "winetricks")
    assert deps._is_exec(tmp_path / "tools" / "winetricks")
    # Panggilan kedua memakai salinan terkelola tanpa unduh ulang.
    assert deps.ensure_winetricks(opener=fake_opener) == path
    assert len(calls) == 1


def test_installed_verbs_reads_log(tmp_path):
    (tmp_path / "winetricks.log").write_text(
        "corefonts\nvcrun2019\nremove_mono internal\n")
    verbs = winetools.installed_verbs(_app(prefix=str(tmp_path)))
    assert {"corefonts", "vcrun2019", "remove_mono"} <= verbs


def test_installed_verbs_missing_log_is_empty(tmp_path):
    assert winetools.installed_verbs(_app(prefix=str(tmp_path))) == set()


def test_ensure_winetricks_prefers_system_binary(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AGUSEMU_WINETRICKS", raising=False)
    monkeypatch.setattr(shutil, "which", lambda _n: "/usr/bin/winetricks")

    def fail_opener(url, timeout=0):
        raise AssertionError("tidak boleh mengunduh bila sudah ada di PATH")

    assert deps.ensure_winetricks(opener=fail_opener) == "/usr/bin/winetricks"

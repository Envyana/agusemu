"""Test regresi untuk perbaikan stabilitas."""
import hashlib
import io
import json
import tarfile

import pytest
from agusemu import config, library, runtimes
from agusemu.models import App


def _use_tmp_data(monkeypatch, tmp_path):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))


def _app(app_id="a-1", **kw):
    base = dict(id=app_id, name="A", exe_path="/a.exe", runtime="r",
                prefix="/pfx/a-1")
    base.update(kw)
    return App(**base)


# --- config / library: korupsi tidak boleh membuat aplikasi gagal start ---

def test_load_config_corrupt_returns_default(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    config.config_path().write_text("{ bukan json")
    assert config.load_config() == config.DEFAULT_CONFIG
    # File korup diamankan sebagai backup, tidak dibiarkan meracuni start.
    assert (tmp_path / "config.json.corrupt").exists()


def test_load_config_null_extra_dirs_sanitized(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    config.config_path().write_text('{"extra_runtime_dirs": null}')
    assert config.load_config()["extra_runtime_dirs"] == []
    # scan_runtimes tidak boleh crash karena nilai null tersebut.
    assert runtimes.scan_runtimes() == []


def test_load_apps_corrupt_returns_empty_and_backs_up(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    config.library_path().write_text("{ terpotong")
    assert library.load_apps() == []
    assert (tmp_path / "library.json.corrupt").exists()


def test_load_apps_skips_malformed_entry(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    payload = {"apps": [_app().to_dict(), {"name": "tanpa field wajib"},
                        "bukan-dict", 42, None]}
    config.library_path().write_text(json.dumps(payload))
    apps = library.load_apps()
    assert [a.id for a in apps] == ["a-1"]


def test_save_apps_is_atomic_no_leftover_tmp(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    library.save_apps([_app()])
    assert [a.id for a in library.load_apps()] == ["a-1"]
    leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


# --- set_runtime: update dari worker thread tidak menimpa editan lain ---

def test_set_runtime_only_touches_runtime_field(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    library.save_apps([_app(runtime="")])
    # Simulasi: pengguna mengedit args selama unduhan runtime berlangsung.
    library.update_app(_app(runtime="", args="--fps 60"))
    library.set_runtime("a-1", "GE-Proton10-1")
    saved = library.get_app("a-1")
    assert saved.runtime == "GE-Proton10-1"
    assert saved.args == "--fps 60"


def test_set_runtime_missing_app_is_noop(tmp_path, monkeypatch):
    _use_tmp_data(monkeypatch, tmp_path)
    library.set_runtime("tidak-ada", "GE-Proton10-1")  # tidak boleh melempar
    assert library.load_apps() == []


# --- extract_tarball: gagal validasi tidak meninggalkan folder parsial ---

def _tarball_bytes(entries):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in entries:
            payload = b"#!/bin/sh\n"
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


def test_extract_tarball_multi_root_leaves_no_partial_dir(tmp_path):
    tb = tmp_path / "rt.tar.gz"
    tb.write_bytes(_tarball_bytes(["A/proton", "B/proton"]))
    dest = tmp_path / "out"
    dest.mkdir()
    with pytest.raises(RuntimeError):
        runtimes.extract_tarball(tb, dest)
    # Folder setengah jadi tidak boleh tersisa dan dianggap runtime valid.
    assert list(dest.iterdir()) == []


def test_extract_tarball_replaces_existing_dir(tmp_path):
    tb = tmp_path / "rt.tar.gz"
    tb.write_bytes(_tarball_bytes(["GE-Proton9-27/proton"]))
    dest = tmp_path / "out"
    (dest / "GE-Proton9-27").mkdir(parents=True)
    (dest / "GE-Proton9-27" / "sisa-lama").write_text("x")
    result = runtimes.extract_tarball(tb, dest)
    assert (result / "proton").exists()
    assert not (result / "sisa-lama").exists()


# --- verify_sha512: file checksum multi-baris dicocokkan per nama aset ---

def test_verify_sha512_multiline_matches_asset(tmp_path):
    f = tmp_path / "a.tar.gz"
    f.write_bytes(b"isi")
    good = hashlib.sha512(b"isi").hexdigest()
    text = (f"{'0' * 128}  lain.tar.xz\n"
            f"{good}  a.tar.gz\n")
    assert runtimes.verify_sha512(f, text, asset_name="a.tar.gz")
    assert not runtimes.verify_sha512(f, text, asset_name="lain.tar.xz")


def test_verify_sha512_empty_text_fails(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"x")
    assert not runtimes.verify_sha512(f, "")


# --- entry point & CLI ---

def test_main_run_without_app_id_returns_usage_error():
    from agusemu import main as main_mod
    assert main_mod.main(["agusemu", "--run"]) == 2


def test_cli_add_duplicate_reports_cleanly(tmp_path, monkeypatch, capsys):
    _use_tmp_data(monkeypatch, tmp_path)
    from agusemu import cli
    args = ["add", "--name", "Notepad", "--exe", "/n.exe", "--runtime", "r"]
    assert cli.main(args) == 0
    assert cli.main(args) == 1
    assert "sudah ada" in capsys.readouterr().out

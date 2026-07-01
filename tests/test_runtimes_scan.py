from pathlib import Path
from agusemu import runtimes


def _make_rt(base: Path, name: str):
    d = base / name
    d.mkdir(parents=True)
    (d / "proton").write_text("#!/bin/sh\n")
    return d


def test_is_runtime_dir(tmp_path):
    d = _make_rt(tmp_path, "GE-Proton9-27")
    assert runtimes.is_runtime_dir(d)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert not runtimes.is_runtime_dir(empty)


def test_scan_managed(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    _make_rt(tmp_path / "runtimes", "GE-Proton9-27")
    _make_rt(tmp_path / "runtimes", "GE-Proton10-1")
    names = [r.name for r in runtimes.scan_runtimes()]
    assert names == ["GE-Proton10-1", "GE-Proton9-27"]


def test_scan_includes_extra_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    ext = tmp_path / "ext"
    _make_rt(ext, "GE-Proton8-32")
    from agusemu import config
    config.save_config({"extra_runtime_dirs": [str(ext)], "default_runtime": None})
    names = [r.name for r in runtimes.scan_runtimes()]
    assert "GE-Proton8-32" in names

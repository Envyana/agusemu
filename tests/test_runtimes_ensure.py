from pathlib import Path
from agusemu import runtimes
from agusemu.models import Runtime
from agusemu.runtimes import Release


def _make_rt(base: Path, name: str):
    d = base / name
    d.mkdir(parents=True)
    (d / "proton").write_text("#!/bin/sh\n")


def test_ensure_uses_named_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    _make_rt(tmp_path / "runtimes", "GE-Proton9-27")
    rt = runtimes.ensure_runtime("GE-Proton9-27")
    assert rt.name == "GE-Proton9-27"


def test_ensure_empty_name_uses_newest(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    _make_rt(tmp_path / "runtimes", "GE-Proton9-27")
    _make_rt(tmp_path / "runtimes", "GE-Proton10-1")
    assert runtimes.ensure_runtime("").name == "GE-Proton10-1"


def test_ensure_downloads_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    calls = {}

    def fake_fetch(limit=30, opener=None):
        return [Release(tag="GE-Proton10-1", tarball_url="u", checksum_url=None)]

    def fake_download(rel, progress=None, opener=None):
        calls["tag"] = rel.tag
        return Runtime(name=rel.tag, path=f"/rt/{rel.tag}", source="managed")

    monkeypatch.setattr(runtimes, "fetch_releases", fake_fetch)
    monkeypatch.setattr(runtimes, "download_runtime", fake_download)
    status = []
    rt = runtimes.ensure_runtime("", on_status=status.append)
    assert rt.name == "GE-Proton10-1"
    assert calls["tag"] == "GE-Proton10-1"
    assert status  # ada pesan status

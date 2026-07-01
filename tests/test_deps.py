import stat
import pytest
from agusemu import deps


def test_find_umu_run_env(tmp_path, monkeypatch):
    fake = tmp_path / "umu-run"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("AGUSEMU_UMU_RUN", str(fake))
    assert deps.find_umu_run() == str(fake)


def test_find_umu_run_none(monkeypatch):
    monkeypatch.delenv("AGUSEMU_UMU_RUN", raising=False)
    monkeypatch.setattr(deps.shutil, "which", lambda name: None)
    monkeypatch.setattr(deps, "_bundled_umu", lambda: None)
    assert deps.find_umu_run() is None


def test_require_umu_run_raises(monkeypatch):
    monkeypatch.setattr(deps, "find_umu_run", lambda: None)
    with pytest.raises(FileNotFoundError):
        deps.require_umu_run()

import json
from agusemu import config


def test_data_dir_honors_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path / "data"))
    d = config.data_dir()
    assert d == tmp_path / "data"
    assert d.is_dir()


def test_subdirs_created(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path / "data"))
    assert config.runtimes_dir().is_dir()
    assert config.prefixes_dir().is_dir()


def test_load_config_default_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path / "data"))
    cfg = config.load_config()
    assert cfg == {"extra_runtime_dirs": [], "default_runtime": None}


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path / "data"))
    config.save_config({"extra_runtime_dirs": ["/opt/ge"], "default_runtime": "GE-Proton9-27"})
    cfg = config.load_config()
    assert cfg["extra_runtime_dirs"] == ["/opt/ge"]
    assert cfg["default_runtime"] == "GE-Proton9-27"
    assert json.loads(config.config_path().read_text())

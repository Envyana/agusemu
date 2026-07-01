import pytest
from agusemu import library
from agusemu.models import App


def _app(app_id="a-1", name="A"):
    return App(id=app_id, name=name, exe_path="/x.exe",
               runtime="r", prefix="/p/" + app_id)


def test_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    assert library.load_apps() == []


def test_add_and_get(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    library.add_app(_app())
    assert library.get_app("a-1").name == "A"
    assert len(library.load_apps()) == 1


def test_add_duplicate_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    library.add_app(_app())
    with pytest.raises(ValueError):
        library.add_app(_app())


def test_update_replaces(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    library.add_app(_app())
    library.update_app(_app().with_changes(name="B"))
    assert library.get_app("a-1").name == "B"


def test_update_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    with pytest.raises(KeyError):
        library.update_app(_app())


def test_remove(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    library.add_app(_app())
    library.remove_app("a-1")
    assert library.get_app("a-1") is None

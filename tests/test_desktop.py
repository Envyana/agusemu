from agusemu import desktop
from agusemu.models import App


def _app():
    return App(id="a-1", name="Game A", exe_path="/g/a.exe",
               runtime="r", prefix="/pfx/a-1")


def test_desktop_entry_text():
    txt = desktop.desktop_entry_text(_app(), "agusemu --run a-1", "/i/a.png")
    assert "[Desktop Entry]" in txt
    assert "Name=Game A" in txt
    assert "Exec=agusemu --run a-1" in txt
    assert "Icon=/i/a.png" in txt


def test_create_shortcut_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path / "AgusEmu"))
    icon = tmp_path / "src.png"
    icon.write_bytes(b"\x89PNG\r\n")
    path = desktop.create_shortcut(_app(), "agusemu --run a-1", icon_src=str(icon))
    assert path.exists()
    assert path.name == "agusemu-a-1.desktop"
    assert "Name=Game A" in path.read_text()

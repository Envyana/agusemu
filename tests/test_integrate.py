from pathlib import Path
from agusemu import integrate


def test_noop_without_appimage(monkeypatch):
    monkeypatch.delenv("APPIMAGE", raising=False)
    assert integrate.integrate_appimage("/x.png") is False


def test_installs_desktop_and_icon(tmp_path, monkeypatch):
    appimage = tmp_path / "AgusEmu.AppImage"
    appimage.write_text("x")
    logo = tmp_path / "logo.png"
    logo.write_bytes(b"\x89PNG\r\n")
    monkeypatch.setenv("APPIMAGE", str(appimage))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "share"))
    assert integrate.integrate_appimage(logo) is True
    desktop = tmp_path / "share" / "applications" / "com.patopo.AgusEmu.desktop"
    icon = tmp_path / "share" / "icons" / "hicolor" / "256x256" / "apps" / "com.patopo.AgusEmu.png"
    assert desktop.exists() and icon.exists()
    assert f'Exec="{appimage}"' in desktop.read_text()


def test_never_raises_when_do_integrate_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("APPIMAGE", str(tmp_path / "x.AppImage"))

    def boom(*a, **k):
        raise PermissionError("denied")

    monkeypatch.setattr(integrate, "_do_integrate", boom)
    # tidak boleh melempar exception
    assert integrate.integrate_appimage("/x.png") is False

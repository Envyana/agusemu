import importlib
import pytest

gi = pytest.importorskip("gi")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw  # noqa: E402

Adw.init()


def test_main_window_constructs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    mod = importlib.import_module("agusemu.ui.main_window")
    app = Adw.Application(application_id="com.patopo.AgusEmu.Test")
    win = mod.MainWindow(application=app)
    assert win is not None
    win.refresh_library()


def test_detail_view_shows_app(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu import library
    from agusemu.models import App
    from agusemu.ui.detail_view import DetailView
    library.add_app(App(id="a-1", name="Game A", exe_path="/g/a.exe",
                        runtime="GE-Proton9-27", prefix="/pfx/a-1"))
    dv = DetailView(on_launch=lambda a: None, on_edit=lambda a: None,
                    on_winetricks=lambda a: None, on_winecfg=lambda a: None,
                    on_shortcut=lambda a: None, on_remove=lambda a: None)
    dv.show_app(library.get_app("a-1"))
    assert dv is not None


def test_add_app_dialog_constructs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu.models import Runtime
    from agusemu.ui.add_app_dialog import AddAppDialog
    dlg = AddAppDialog(runtimes=[Runtime("GE-Proton9-27", "/rt/x", "managed")],
                       on_save=lambda app: None)
    assert dlg is not None


def test_log_window_append(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu.ui.log_window import LogWindow
    lw = LogWindow(title="Log: Test")
    lw.append_line("baris 1")
    lw.mark_finished(0)
    assert lw is not None


def test_runtime_manager_constructs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu.ui.runtime_manager import RuntimeManager
    assert RuntimeManager() is not None


def test_winetricks_dialog_constructs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu.models import App, Runtime
    from agusemu.ui.winetricks_dialog import WinetricksDialog
    app = App(id="a-1", name="A", exe_path="/a.exe", runtime="r", prefix="/p")
    dlg = WinetricksDialog(app=app, runtime=Runtime("r", "/rt/r", "managed"),
                           on_run=lambda verbs: None)
    assert dlg is not None


def test_logo_asset_and_empty_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from gi.repository import Gdk
    from agusemu.ui.main_window import LOGO_PATH, MainWindow
    assert LOGO_PATH.exists()
    tex = Gdk.Texture.new_from_filename(str(LOGO_PATH))
    assert tex.get_width() > 0
    app = Adw.Application(application_id="com.patopo.AgusEmu.Logo")
    win = MainWindow(application=app)
    assert win is not None


def test_install_dialog_constructs(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu.models import Runtime
    from agusemu.ui.install_dialog import InstallDialog
    dlg = InstallDialog(runtimes=[Runtime("GE-Proton9-27", "/rt/x", "managed")],
                        on_install=lambda *a: None)
    assert dlg is not None


def test_sidebar_groups_by_category(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    from agusemu import library
    from agusemu.models import App
    from agusemu.ui.main_window import MainWindow
    library.add_app(App(id="g1", name="Game One", exe_path="/g.exe",
                        runtime="", prefix="/p/g1", category="game"))
    library.add_app(App(id="a1", name="App One", exe_path="/a.exe",
                        runtime="", prefix="/p/a1", category="app"))
    app = Adw.Application(application_id="com.patopo.AgusEmu.Cat")
    win = MainWindow(application=app)
    win.refresh_library()
    # baris pertama harus kategori 'app' (diurutkan app dulu)
    first = win.listbox.get_first_child()
    assert first._category == "app"

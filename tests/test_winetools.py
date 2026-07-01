from agusemu import winetools
from agusemu.models import App, Runtime


def _app():
    return App(id="a-1", name="A", exe_path="/a.exe", runtime="r", prefix="/pfx/a-1")


def _rt():
    return Runtime(name="r", path="/rt/r", source="managed")


def test_winetricks_command():
    cmd, env = winetools.winetricks_command(
        _app(), _rt(), ["corefonts", "vcrun2019"],
        umu_run="/u/umu-run", winetricks="/u/winetricks")
    assert cmd == ["/u/umu-run", "/u/winetricks", "corefonts", "vcrun2019"]
    assert env["PROTONPATH"] == "/rt/r"
    assert env["WINEPREFIX"] == "/pfx/a-1"


def test_winecfg_command():
    cmd, env = winetools.winecfg_command(_app(), _rt(), umu_run="/u/umu-run")
    assert cmd == ["/u/umu-run", "winecfg"]
    assert env["WINEPREFIX"] == "/pfx/a-1"

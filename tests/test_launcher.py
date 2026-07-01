from agusemu import launcher
from agusemu.models import App, Runtime


def _app(**kw):
    base = dict(id="a-1", name="A", exe_path="/games/a.exe",
                runtime="GE-Proton9-27", prefix="/pfx/a-1")
    base.update(kw)
    return App(**base)


def _rt():
    return Runtime(name="GE-Proton9-27", path="/rt/GE-Proton9-27", source="managed")


def test_build_env_core_vars():
    env = launcher.build_env(_app(), _rt(), base_env={})
    assert env["GAMEID"] == "0"
    assert env["PROTONPATH"] == "/rt/GE-Proton9-27"
    assert env["WINEPREFIX"] == "/pfx/a-1"
    assert env["STEAM_COMPAT_DATA_PATH"] == "/pfx/a-1"
    assert "PROTON_USE_WINED3D" not in env


def test_build_env_dxvk_off_sets_wined3d():
    env = launcher.build_env(_app(dxvk_enabled=False), _rt(), base_env={})
    assert env["PROTON_USE_WINED3D"] == "1"


def test_build_env_custom_env_overrides():
    env = launcher.build_env(_app(env={"DXVK_HUD": "fps"}), _rt(), base_env={})
    assert env["DXVK_HUD"] == "fps"


def test_build_env_does_not_mutate_base():
    base = {"HOME": "/home/x"}
    launcher.build_env(_app(), _rt(), base_env=base)
    assert base == {"HOME": "/home/x"}


def test_build_command_with_args():
    cmd = launcher.build_command(_app(args='--foo "bar baz"'), "/usr/bin/umu-run")
    assert cmd == ["/usr/bin/umu-run", "/games/a.exe", "--foo", "bar baz"]

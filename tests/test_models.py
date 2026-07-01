from agusemu.models import App, Runtime, make_app_id


def test_make_app_id_is_slug_with_hash():
    a = make_app_id("Notepad++")
    assert a.startswith("notepad")
    assert "-" in a
    assert make_app_id("Notepad++") == a
    assert make_app_id("Notepad") != a


def test_app_roundtrip_dict():
    app = App(id="x-abc123", name="X", exe_path="/g/x.exe",
              runtime="GE-Proton9-27", prefix="/p/x-abc123",
              env={"DXVK_HUD": "fps"}, created_at="2026-07-01")
    d = app.to_dict()
    assert App.from_dict(d) == app


def test_app_with_changes_is_immutable():
    app = App(id="x", name="X", exe_path="/x.exe", runtime="r", prefix="/p")
    updated = app.with_changes(name="Y")
    assert updated.name == "Y"
    assert app.name == "X"


def test_runtime_proton_binary():
    rt = Runtime(name="GE-Proton9-27", path="/rt/GE-Proton9-27", source="managed")
    assert rt.proton_binary().endswith("/GE-Proton9-27/proton")

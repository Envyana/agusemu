from agusemu import cli


def test_add_and_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    rc = cli.main(["add", "--name", "MyApp", "--exe", "/g/a.exe",
                   "--runtime", "GE-Proton9-27"])
    assert rc == 0
    app_id = capsys.readouterr().out.strip().splitlines()[-1].strip()
    assert app_id
    rc = cli.main(["list"])
    assert rc == 0
    listing = capsys.readouterr().out
    assert "MyApp" in listing and app_id in listing


def test_runtimes_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    assert cli.main(["runtimes"]) == 0

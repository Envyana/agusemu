from agusemu import icons


def test_extract_returns_none_for_non_pe(tmp_path):
    f = tmp_path / "not.exe"
    f.write_bytes(b"this is not a PE file")
    assert icons.extract_exe_icon(f, tmp_path / "out.png") is None


def test_extract_returns_none_for_missing_file(tmp_path):
    assert icons.extract_exe_icon(tmp_path / "nope.exe", tmp_path / "out.png") is None

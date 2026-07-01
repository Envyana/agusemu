import hashlib
import io
import tarfile
from pathlib import Path

import pytest
from agusemu import runtimes
from agusemu.runtimes import Release


class Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def test_verify_sha512(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello")
    h = hashlib.sha512(b"hello").hexdigest()
    assert runtimes.verify_sha512(f, f"{h}  a.bin")
    assert not runtimes.verify_sha512(f, "deadbeef  a.bin")


def _tarball_bytes(top="GE-Proton9-27", payload=b"#!/bin/sh\n"):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(f"{top}/proton")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


def test_extract_tarball(tmp_path):
    tb = tmp_path / "rt.tar.gz"
    tb.write_bytes(_tarball_bytes())
    dest = tmp_path / "out"
    dest.mkdir()
    result = runtimes.extract_tarball(tb, dest)
    assert result.name == "GE-Proton9-27"
    assert (result / "proton").exists()


def test_download_runtime_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    raw = _tarball_bytes()
    checksum = hashlib.sha512(raw).hexdigest() + "  GE-Proton9-27.tar.gz\n"

    def fake_opener(url, timeout=0):
        if url.endswith(".sha512sum"):
            return Resp(checksum.encode())
        return Resp(raw)

    rel = Release(tag="GE-Proton9-27",
                  tarball_url="https://x/GE-Proton9-27.tar.gz",
                  checksum_url="https://x/GE-Proton9-27.sha512sum")
    rt = runtimes.download_runtime(rel, opener=fake_opener)
    assert rt.name == "GE-Proton9-27"
    assert Path(rt.path, "proton").exists()
    assert rt.source == "managed"


def test_download_runtime_bad_checksum(tmp_path, monkeypatch):
    monkeypatch.setenv("AGUSEMU_DATA_DIR", str(tmp_path))
    raw = _tarball_bytes()

    def fake_opener(url, timeout=0):
        if url.endswith(".sha512sum"):
            return Resp(b"deadbeef  GE-Proton9-27.tar.gz\n")
        return Resp(raw)

    rel = Release(tag="GE-Proton9-27", tarball_url="https://x/x.tar.gz",
                  checksum_url="https://x/x.sha512sum")
    with pytest.raises(RuntimeError):
        runtimes.download_runtime(rel, opener=fake_opener)

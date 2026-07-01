import io
import json
from agusemu import runtimes

SAMPLE = [
    {"tag_name": "GE-Proton10-1", "assets": [
        {"name": "GE-Proton10-1.tar.gz",
         "browser_download_url": "https://x/GE-Proton10-1.tar.gz"},
        {"name": "GE-Proton10-1.sha512sum",
         "browser_download_url": "https://x/GE-Proton10-1.sha512sum"},
    ]},
    {"tag_name": "no-tarball", "assets": [
        {"name": "notes.txt", "browser_download_url": "https://x/notes.txt"},
    ]},
]


def test_parse_releases_picks_tarball_and_checksum():
    rels = runtimes.parse_releases(SAMPLE)
    assert len(rels) == 1
    assert rels[0].tag == "GE-Proton10-1"
    assert rels[0].tarball_url.endswith("GE-Proton10-1.tar.gz")
    assert rels[0].checksum_url.endswith(".sha512sum")


def test_fetch_releases_uses_opener_and_limit():
    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): self.close()
    def fake_opener(url, timeout=0):
        assert "GloriousEggroll" in url
        return Resp(json.dumps(SAMPLE).encode())
    rels = runtimes.fetch_releases(limit=1, opener=fake_opener)
    assert len(rels) == 1
    assert rels[0].tag == "GE-Proton10-1"

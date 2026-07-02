"""Best-effort icon extraction from a Windows PE (.exe/.dll).

Pure-Python PE resource parsing; converts the largest embedded icon to PNG via
PIL when available. Returns None on any failure so callers fall back to a
default icon. Never raises.
"""
from __future__ import annotations

import io
import mmap
import struct
from pathlib import Path

RT_ICON = 3
RT_GROUP_ICON = 14


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _sections(data):
    e = _u32(data, 0x3C)
    if data[e:e + 4] != b"PE\x00\x00":
        return None, None, None
    coff = e + 4
    nsec = _u16(data, coff + 2)
    sz_opt = _u16(data, coff + 16)
    opt = coff + 20
    magic = _u16(data, opt)
    dd = opt + (96 if magic == 0x10B else 112)
    res_rva = _u32(data, dd + 2 * 8)
    secs = []
    base = opt + sz_opt
    for i in range(nsec):
        so = base + i * 40
        secs.append((_u32(data, so + 12), _u32(data, so + 16), _u32(data, so + 20)))
    return secs, res_rva, magic


def _rva_off(secs, rva):
    for va, size, ptr in secs:
        if va <= rva < va + (size or 1):
            return ptr + (rva - va)
    return None


def _entries(data, off):
    n = _u16(data, off + 12) + _u16(data, off + 14)
    out = []
    eo = off + 16
    for _ in range(n):
        out.append((_u32(data, eo), _u32(data, eo + 4)))
        eo += 8
    return out


def _leaf_data(data, secs, res_off, entry_off):
    de = res_off + (entry_off & 0x7FFFFFFF)
    rva = _u32(data, de)
    size = _u32(data, de + 4)
    o = _rva_off(secs, rva)
    return data[o:o + size] if o is not None else None


def _collect(data, secs, res_off, type_id):
    """Return {resource_id: bytes} for a resource type."""
    result = {}
    for nm, off in _entries(data, res_off):
        if nm == type_id and (off & 0x80000000):
            tdir = res_off + (off & 0x7FFFFFFF)
            for nm2, off2 in _entries(data, tdir):
                if off2 & 0x80000000:
                    ldir = res_off + (off2 & 0x7FFFFFFF)
                    for _nm3, off3 in _entries(data, ldir):
                        if not (off3 & 0x80000000):
                            b = _leaf_data(data, secs, res_off, off3)
                            if b is not None:
                                result[nm2] = b
                            break
    return result


def _build_ico(group, icons) -> bytes | None:
    if len(group) < 6:
        return None
    count = _u16(group, 4)
    header = struct.pack("<HHH", 0, 1, count)
    entries = b""
    images = b""
    offset = 6 + 16 * count
    for i in range(count):
        g = 6 + 14 * i
        if g + 14 > len(group):
            return None
        icon_id = _u16(group, g + 12)
        img = icons.get(icon_id)
        if img is None:
            return None
        entries += group[g:g + 12] + struct.pack("<I", offset)
        images += img
        offset += len(img)
    return header + entries + images


def extract_exe_icon(exe_path: str | Path, dest_png: str | Path) -> Path | None:
    try:
        # mmap, bukan read_bytes(): exe game bisa berukuran multi-GB dan
        # tidak boleh dimuat utuh ke RAM hanya untuk mengambil ikon.
        with open(exe_path, "rb") as fh, \
                mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as data:
            secs, res_rva, _ = _sections(data)
            if not secs or not res_rva:
                return None
            res_off = _rva_off(secs, res_rva)
            if res_off is None:
                return None
            groups = _collect(data, secs, res_off, RT_GROUP_ICON)
            icons = _collect(data, secs, res_off, RT_ICON)
            if not groups or not icons:
                return None
            ico = _build_ico(next(iter(groups.values())), icons)
        if not ico:
            return None
        from PIL import Image  # noqa: E402 — import malas, PIL opsional
        im = Image.open(io.BytesIO(ico))
        # pick largest available size
        if getattr(im, "ico", None):
            im = im.ico.getimage(max(im.ico.sizes()))
        dest = Path(dest_png)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.convert("RGBA").save(dest)
        return dest
    except Exception:
        return None

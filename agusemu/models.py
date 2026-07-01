"""Model data immutable untuk AgusEmu."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

CATEGORIES = ("app", "game")


def make_app_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{digest}"


@dataclass(frozen=True)
class App:
    id: str
    name: str
    exe_path: str
    runtime: str
    prefix: str
    icon: str = ""
    args: str = ""
    env: dict[str, str] = field(default_factory=dict)
    dxvk_enabled: bool = True
    category: str = "app"  # "app" | "game"
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "App":
        allowed = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in d.items() if k in allowed})

    def with_changes(self, **kw) -> "App":
        return replace(self, **kw)


@dataclass(frozen=True)
class Runtime:
    name: str
    path: str
    source: str  # "local" | "managed"

    def proton_binary(self) -> str:
        return str(Path(self.path) / "proton")

"""CLI ringan untuk menguji core AgusEmu tanpa GUI."""
from __future__ import annotations

import argparse
import datetime as _dt

from . import config, launcher, library, runtimes
from .models import App, Runtime, make_app_id


def _today() -> str:
    return _dt.date.today().isoformat()


def _find_runtime(name: str) -> Runtime | None:
    for rt in runtimes.scan_runtimes():
        if rt.name == name:
            return rt
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agusemu-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("runtimes")
    sub.add_parser("list")
    p_add = sub.add_parser("add")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--exe", required=True)
    p_add.add_argument("--runtime", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("app_id")

    ns = parser.parse_args(argv)

    if ns.cmd == "runtimes":
        for rt in runtimes.scan_runtimes():
            print(rt.name)
        return 0

    if ns.cmd == "list":
        for a in library.load_apps():
            print(f"{a.id}\t{a.name}\t{a.runtime}")
        return 0

    if ns.cmd == "add":
        app_id = make_app_id(ns.name)
        app = App(id=app_id, name=ns.name, exe_path=ns.exe, runtime=ns.runtime,
                  prefix=str(config.prefixes_dir() / app_id), created_at=_today())
        library.add_app(app)
        print(app_id)
        return 0

    if ns.cmd == "run":
        app = library.get_app(ns.app_id)
        if not app:
            print(f"App tidak ditemukan: {ns.app_id}")
            return 1
        rt = _find_runtime(app.runtime)
        if not rt:
            print(f"Runtime tidak ditemukan: {app.runtime}")
            return 1
        return launcher.launch(app, rt, on_output=print)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

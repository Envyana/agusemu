"""Entry point AgusEmu (GTK4/libadwaita)."""
from __future__ import annotations

import sys

APP_ID = "com.patopo.AgusEmu"


def _run_headless(app_id: str) -> int:
    from . import launcher, library
    from .cli import _find_runtime
    app = library.get_app(app_id)
    if not app:
        print(f"App not found: {app_id}", file=sys.stderr)
        return 1
    rt = _find_runtime(app.runtime)
    if not rt:
        print(f"Runtime not found: {app.runtime}", file=sys.stderr)
        return 1
    return launcher.launch(app, rt, on_output=print)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if "--run" in argv:
        return _run_headless(argv[argv.index("--run") + 1])

    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio
    from .integrate import integrate_appimage
    from .ui.main_window import LOGO_PATH, MainWindow
    integrate_appimage(LOGO_PATH)

    app = Adw.Application(application_id=APP_ID,
                          flags=Gio.ApplicationFlags.FLAGS_NONE)

    def on_activate(a):
        win = a.get_active_window() or MainWindow(application=a)
        win.present()

    app.connect("activate", on_activate)
    return app.run([])


if __name__ == "__main__":
    raise SystemExit(main())

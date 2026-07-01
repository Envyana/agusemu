"""Detail panel for a single application."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from ..models import App  # noqa: E402


class DetailView(Gtk.Box):
    def __init__(self, on_launch, on_edit, on_winetricks,
                 on_winecfg, on_shortcut, on_remove):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                         margin_top=24, margin_bottom=24,
                         margin_start=24, margin_end=24)
        self._app: App | None = None
        self._cb = dict(launch=on_launch, edit=on_edit, winetricks=on_winetricks,
                        winecfg=on_winecfg, shortcut=on_shortcut, remove=on_remove)

        self.title = Gtk.Label(xalign=0)
        self.title.add_css_class("title-1")
        self.append(self.title)

        self.subtitle = Gtk.Label(xalign=0, wrap=True)
        self.subtitle.add_css_class("dim-label")
        self.append(self.subtitle)

        self.launch_btn = Gtk.Button(label="Launch")
        self.launch_btn.add_css_class("suggested-action")
        self.launch_btn.add_css_class("pill")
        self.launch_btn.set_halign(Gtk.Align.START)
        self.launch_btn.connect("clicked", lambda *_: self._emit("launch"))
        self.append(self.launch_btn)

        group = Adw.PreferencesGroup(title="Actions")
        self.append(group)
        for key, label in [("winetricks", "Winetricks / Components"),
                           ("winecfg", "Open winecfg"),
                           ("shortcut", "Create Menu Shortcut"),
                           ("edit", "Edit"),
                           ("remove", "Remove")]:
            row = Adw.ActionRow(title=label, activatable=True)
            row.connect("activated", lambda _r, k=key: self._emit(k))
            group.add(row)

    def _emit(self, key):
        if self._app is not None:
            self._cb[key](self._app)

    def show_app(self, app: App):
        self._app = app
        self.title.set_text(app.name)
        self.subtitle.set_text(f"{app.exe_path}\nRuntime: {app.runtime or 'Automatic'}")

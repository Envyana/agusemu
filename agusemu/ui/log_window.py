"""Real-time log window for umu-run processes."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402


class LogWindow(Adw.Window):
    def __init__(self, title: str = "Log", **kwargs):
        super().__init__(**kwargs)
        self.set_title(title)
        self.set_default_size(720, 460)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.buffer = Gtk.TextBuffer()
        view = Gtk.TextView(buffer=self.buffer, editable=False, monospace=True)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll = Gtk.ScrolledWindow(child=view)
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)
        self.set_content(toolbar)

    def append_line(self, text: str):
        def _do():
            self.buffer.insert(self.buffer.get_end_iter(), text + "\n")
            return False
        GLib.idle_add(_do)

    def mark_finished(self, code: int):
        self.append_line(f"\n[finished] exit code = {code}")

"""Log window that tails a file at a fixed rate (flood-proof)."""
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
        self._timer = None
        self._path = None
        self._pos = 0

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.buffer = Gtk.TextBuffer()
        self._view = Gtk.TextView(buffer=self.buffer, editable=False, monospace=True)
        self._view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll = Gtk.ScrolledWindow(child=self._view)
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)
        self.set_content(toolbar)
        self.connect("close-request", self._on_close)

    def tail_file(self, path: str):
        """Poll `path` twice a second and append new content. Fixed-rate updates
        mean a very chatty process can't flood the GTK main loop."""
        self._path = path
        self._pos = 0
        self._timer = GLib.timeout_add(500, self._poll)

    def _poll(self):
        if not self._path:
            return False
        try:
            with open(self._path) as f:
                f.seek(self._pos)
                data = f.read()
                self._pos = f.tell()
        except OSError:
            return True
        if data:
            self.buffer.insert(self.buffer.get_end_iter(), data)
            mark = self.buffer.create_mark(None, self.buffer.get_end_iter(), False)
            self._view.scroll_mark_onscreen(mark)
        return True

    def _on_close(self, *_):
        if self._timer is not None:
            GLib.source_remove(self._timer)
            self._timer = None
        return False

    # kept for compatibility (append a single line immediately)
    def append_line(self, text: str):
        GLib.idle_add(lambda: (self.buffer.insert(
            self.buffer.get_end_iter(), text + "\n"), False)[1])

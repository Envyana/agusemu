"""Dialog untuk menjalankan installer .exe lalu memilih program hasilnya."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from ..models import Runtime  # noqa: E402
from .add_app_dialog import (build_category_row, build_runtime_row,  # noqa: E402
                             selected_category, selected_runtime_name)


class InstallDialog(Adw.Dialog):
    """Kumpulkan nama, installer .exe, kategori, runtime; panggil on_install(...)."""

    def __init__(self, runtimes: list[Runtime], on_install):
        super().__init__()
        self._on_install = on_install
        self._runtimes = runtimes
        self._installer = ""
        self.set_title("Install Program (.exe)")
        self.set_content_width(460)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        run = Gtk.Button(label="Install")
        run.add_css_class("suggested-action")
        run.connect("clicked", self._on_install_clicked)
        header.pack_end(run)
        toolbar.add_top_bar(header)

        group = Adw.PreferencesGroup(margin_top=12, margin_bottom=12,
                                     margin_start=12, margin_end=12,
                                     description="Jalankan installer di prefix baru, "
                                                 "lalu pilih program hasil instalnya.")
        self.name_row = Adw.EntryRow(title="Nama program")
        group.add(self.name_row)

        self.exe_row = Adw.ActionRow(title="Installer .exe", subtitle="Belum dipilih")
        pick = Gtk.Button(label="Pilih", valign=Gtk.Align.CENTER)
        pick.connect("clicked", self._on_pick)
        self.exe_row.add_suffix(pick)
        group.add(self.exe_row)

        self.category_row = build_category_row("app")
        group.add(self.category_row)
        self.runtime_row = build_runtime_row(runtimes, "")
        group.add(self.runtime_row)

        toolbar.set_content(group)
        self.set_child(toolbar)

    def _on_pick(self, _btn):
        dialog = Gtk.FileDialog(title="Pilih installer .exe")
        filt = Gtk.FileFilter()
        filt.set_name("Executable Windows")
        filt.add_pattern("*.exe")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filt)
        dialog.set_filters(filters)

        def done(dlg, res):
            try:
                f = dlg.open_finish(res)
            except Exception:
                return
            if f:
                self._installer = f.get_path()
                self.exe_row.set_subtitle(self._installer)

        dialog.open(self.get_root(), None, done)

    def _on_install_clicked(self, _btn):
        name = self.name_row.get_text().strip()
        if not name or not self._installer:
            return
        self._on_install(
            name,
            self._installer,
            selected_category(self.category_row),
            selected_runtime_name(self.runtime_row, self._runtimes),
        )
        self.close()

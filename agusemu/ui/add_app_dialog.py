"""Dialog tambah/edit aplikasi."""
from __future__ import annotations

import datetime as _dt

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from .. import config  # noqa: E402
from ..models import App, Runtime, make_app_id  # noqa: E402


class AddAppDialog(Adw.Dialog):
    def __init__(self, runtimes: list[Runtime], on_save, app: App | None = None):
        super().__init__()
        self._on_save = on_save
        self._app = app
        self._runtimes = runtimes
        self._exe_path = app.exe_path if app else ""
        self.set_title("Edit Aplikasi" if app else "Tambah Aplikasi")
        self.set_content_width(460)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        save = Gtk.Button(label="Simpan")
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save_clicked)
        header.pack_end(save)
        toolbar.add_top_bar(header)

        group = Adw.PreferencesGroup(margin_top=12, margin_bottom=12,
                                     margin_start=12, margin_end=12)
        self.name_row = Adw.EntryRow(title="Nama")
        if app:
            self.name_row.set_text(app.name)
        group.add(self.name_row)

        self.exe_row = Adw.ActionRow(title="File .exe",
                                     subtitle=self._exe_path or "Belum dipilih")
        pick = Gtk.Button(label="Pilih", valign=Gtk.Align.CENTER)
        pick.connect("clicked", self._on_pick_exe)
        self.exe_row.add_suffix(pick)
        group.add(self.exe_row)

        self.runtime_row = Adw.ComboRow(title="Runtime GE-Proton")
        model = Gtk.StringList()
        for rt in runtimes:
            model.append(rt.name)
        self.runtime_row.set_model(model)
        if app:
            for i, rt in enumerate(runtimes):
                if rt.name == app.runtime:
                    self.runtime_row.set_selected(i)
        group.add(self.runtime_row)

        self.args_row = Adw.EntryRow(title="Argumen (opsional)")
        if app:
            self.args_row.set_text(app.args)
        group.add(self.args_row)

        self.dxvk_row = Adw.SwitchRow(title="Aktifkan DXVK/VKD3D")
        self.dxvk_row.set_active(app.dxvk_enabled if app else True)
        group.add(self.dxvk_row)

        toolbar.set_content(group)
        self.set_child(toolbar)

    def _on_pick_exe(self, _btn):
        dialog = Gtk.FileDialog(title="Pilih file .exe")
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
                self._exe_path = f.get_path()
                self.exe_row.set_subtitle(self._exe_path)

        dialog.open(self.get_root(), None, done)

    def _selected_runtime_name(self) -> str:
        idx = self.runtime_row.get_selected()
        if 0 <= idx < len(self._runtimes):
            return self._runtimes[idx].name
        return ""

    def _on_save_clicked(self, _btn):
        name = self.name_row.get_text().strip()
        if not name or not self._exe_path:
            return
        runtime = self._selected_runtime_name()
        args = self.args_row.get_text()
        dxvk = self.dxvk_row.get_active()
        if self._app:
            app = self._app.with_changes(name=name, exe_path=self._exe_path,
                                         runtime=runtime, args=args, dxvk_enabled=dxvk)
        else:
            app_id = make_app_id(name)
            app = App(id=app_id, name=name, exe_path=self._exe_path, runtime=runtime,
                      prefix=str(config.prefixes_dir() / app_id), args=args,
                      dxvk_enabled=dxvk, created_at=_dt.date.today().isoformat())
        self._on_save(app)
        self.close()

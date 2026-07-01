"""Add/edit application dialog."""
from __future__ import annotations

import datetime as _dt

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402

from .. import config  # noqa: E402
from ..models import App, Runtime, make_app_id  # noqa: E402

AUTO_LABEL = "Automatic (download latest GE-Proton)"
_CATS = [("app", "Everyday application"), ("game", "Game")]


def make_exe_filter():
    filt = Gtk.FileFilter()
    filt.set_name("Windows program / installer")
    filt.add_pattern("*.exe")
    filt.add_pattern("*.msi")
    filters = Gio.ListStore.new(Gtk.FileFilter)
    filters.append(filt)
    return filters


def build_runtime_row(runtimes: list[Runtime], current: str = ""):
    row = Adw.ComboRow(title="GE-Proton runtime")
    model = Gtk.StringList()
    model.append(AUTO_LABEL)
    for rt in runtimes:
        model.append(rt.name)
    row.set_model(model)
    if current:
        for i, rt in enumerate(runtimes):
            if rt.name == current:
                row.set_selected(i + 1)
    return row


def selected_runtime_name(row, runtimes: list[Runtime]) -> str:
    idx = row.get_selected()
    if idx <= 0:
        return ""
    if 1 <= idx <= len(runtimes):
        return runtimes[idx - 1].name
    return ""


def build_category_row(current: str = "app"):
    row = Adw.ComboRow(title="Category")
    model = Gtk.StringList()
    for _key, label in _CATS:
        model.append(label)
    row.set_model(model)
    for i, (key, _label) in enumerate(_CATS):
        if key == current:
            row.set_selected(i)
    return row


def selected_category(row) -> str:
    idx = row.get_selected()
    if 0 <= idx < len(_CATS):
        return _CATS[idx][0]
    return "app"


class AddAppDialog(Adw.Dialog):
    def __init__(self, runtimes: list[Runtime], on_save, app: App | None = None):
        super().__init__()
        self._on_save = on_save
        self._app = app
        self._runtimes = runtimes
        self._exe_path = app.exe_path if app else ""
        self.set_title("Edit Application" if app else "Add Application")
        self.set_content_width(460)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        save = Gtk.Button(label="Save")
        save.add_css_class("suggested-action")
        save.connect("clicked", self._on_save_clicked)
        header.pack_end(save)
        toolbar.add_top_bar(header)

        group = Adw.PreferencesGroup(margin_top=12, margin_bottom=12,
                                     margin_start=12, margin_end=12)
        self.name_row = Adw.EntryRow(title="Name")
        if app:
            self.name_row.set_text(app.name)
        group.add(self.name_row)

        self.exe_row = Adw.ActionRow(title="Program (.exe / .msi)",
                                     subtitle=self._exe_path or "Not selected")
        pick = Gtk.Button(label="Choose", valign=Gtk.Align.CENTER)
        pick.connect("clicked", self._on_pick_exe)
        self.exe_row.add_suffix(pick)
        group.add(self.exe_row)

        self.category_row = build_category_row(app.category if app else "app")
        group.add(self.category_row)

        self.runtime_row = build_runtime_row(runtimes, app.runtime if app else "")
        group.add(self.runtime_row)

        self.args_row = Adw.EntryRow(title="Arguments (optional)")
        if app:
            self.args_row.set_text(app.args)
        group.add(self.args_row)

        self.dxvk_row = Adw.SwitchRow(title="Enable DXVK/VKD3D")
        self.dxvk_row.set_active(app.dxvk_enabled if app else True)
        group.add(self.dxvk_row)

        toolbar.set_content(group)
        self.set_child(toolbar)

    def _on_pick_exe(self, _btn):
        dialog = Gtk.FileDialog(title="Choose a program (.exe / .msi)")
        dialog.set_filters(make_exe_filter())

        def done(dlg, res):
            try:
                f = dlg.open_finish(res)
            except Exception:
                return
            if f:
                self._exe_path = f.get_path()
                self.exe_row.set_subtitle(self._exe_path)

        dialog.open(self.get_root(), None, done)

    def _on_save_clicked(self, _btn):
        name = self.name_row.get_text().strip()
        if not name or not self._exe_path:
            return
        runtime = selected_runtime_name(self.runtime_row, self._runtimes)
        category = selected_category(self.category_row)
        args = self.args_row.get_text()
        dxvk = self.dxvk_row.get_active()
        if self._app:
            app = self._app.with_changes(name=name, exe_path=self._exe_path,
                                         runtime=runtime, args=args,
                                         dxvk_enabled=dxvk, category=category)
        else:
            app_id = make_app_id(name)
            app = App(id=app_id, name=name, exe_path=self._exe_path, runtime=runtime,
                      prefix=str(config.prefixes_dir() / app_id), args=args,
                      dxvk_enabled=dxvk, category=category,
                      created_at=_dt.date.today().isoformat())
        self._on_save(app)
        self.close()

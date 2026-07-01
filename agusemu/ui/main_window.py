"""Jendela utama AgusEmu."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from .. import library  # noqa: E402


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("AgusEmu")
        self.set_default_size(960, 640)

        self.split = Adw.NavigationSplitView()

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("navigation-sidebar")
        self.listbox.connect("row-selected", self._on_row_selected)
        sidebar_scroll = Gtk.ScrolledWindow(child=self.listbox)
        sidebar_scroll.set_vexpand(True)
        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Tambah aplikasi")
        add_btn.connect("clicked", lambda *_: self._open_add_dialog())
        sidebar_page = Adw.NavigationPage(
            title="Library",
            child=self._chrome("Library", sidebar_scroll, start_widget=add_btn))
        self.split.set_sidebar(sidebar_page)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.set_vexpand(True)
        self.content_box.append(self._empty_state())
        rt_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        rt_btn.set_tooltip_text("Manajer Runtime")
        rt_btn.connect("clicked", self._open_runtime_manager)
        content_page = Adw.NavigationPage(
            title="AgusEmu",
            child=self._chrome("AgusEmu", self.content_box, end_widget=rt_btn))
        self.split.set_content(content_page)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.split)
        self.set_content(self.toast_overlay)
        self.refresh_library()

    # --- layout helpers ---
    def _chrome(self, title, body, start_widget=None, end_widget=None):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Adw.HeaderBar()
        if start_widget:
            header.pack_start(start_widget)
        if end_widget:
            header.pack_end(end_widget)
        box.append(header)
        body.set_vexpand(True)
        box.append(body)
        return box

    def _empty_state(self):
        return Adw.StatusPage(
            title="Pilih aplikasi",
            description="Tambahkan aplikasi .exe untuk mulai.",
            icon_name="application-x-executable-symbolic")

    def _set_content_child(self, widget):
        child = self.content_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.content_box.remove(child)
            child = nxt
        self.content_box.append(widget)

    def refresh_library(self):
        child = self.listbox.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.listbox.remove(child)
            child = nxt
        for app in library.load_apps():
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=app.name, xalign=0, margin_top=8,
                                    margin_bottom=8, margin_start=12, margin_end=12))
            row._app_id = app.id
            self.listbox.append(row)

    # --- detail wiring ---
    def _make_detail(self):
        from .detail_view import DetailView
        return DetailView(
            on_launch=self._launch_app,
            on_edit=self._open_add_dialog,
            on_winetricks=self._open_winetricks,
            on_winecfg=self._run_winecfg,
            on_shortcut=self._make_shortcut,
            on_remove=self._confirm_remove)

    def _on_row_selected(self, _listbox, row):
        if row is None:
            return
        app = library.get_app(row._app_id)
        if app is None:
            return
        if not hasattr(self, "detail"):
            self.detail = self._make_detail()
        self._set_content_child(self.detail)
        self.detail.show_app(app)

    def _runtime_for(self, app):
        from .. import runtimes as rt_mod
        return next((r for r in rt_mod.scan_runtimes() if r.name == app.runtime), None)

    # --- add/edit ---
    def _open_add_dialog(self, app=None):
        from .. import runtimes as rt_mod
        from .add_app_dialog import AddAppDialog
        AddAppDialog(runtimes=rt_mod.scan_runtimes(),
                     on_save=self._save_app, app=app).present(self)

    def _save_app(self, app):
        if library.get_app(app.id):
            library.update_app(app)
        else:
            library.add_app(app)
        self.refresh_library()

    # --- runtime manager ---
    def _open_runtime_manager(self, *_):
        from .runtime_manager import RuntimeManager
        RuntimeManager().present(self)

    # --- launch ---
    def _launch_app(self, app):
        from .. import launcher
        from .log_window import LogWindow
        rt = self._runtime_for(app)
        log = LogWindow(title=f"Log: {app.name}")
        log.present()
        if rt is None:
            log.append_line(f"Runtime tidak ditemukan: {app.runtime}")
            return

        def worker():
            try:
                code = launcher.launch(app, rt, on_output=log.append_line)
            except Exception as exc:
                log.append_line(f"[error] {exc}")
                code = -1
            log.mark_finished(code)

        threading.Thread(target=worker, daemon=True).start()

    # --- winetricks / winecfg ---
    def _open_winetricks(self, app):
        from .. import winetools
        from .log_window import LogWindow
        from .winetricks_dialog import WinetricksDialog
        rt = self._runtime_for(app)
        if rt is None:
            self._toast(f"Runtime tidak ditemukan: {app.runtime}")
            return

        def on_run(verbs):
            log = LogWindow(title=f"Winetricks: {app.name}")
            log.present()

            def worker():
                try:
                    code = winetools.run_winetricks(app, rt, verbs,
                                                    on_output=log.append_line)
                except Exception as exc:
                    log.append_line(f"[error] {exc}")
                    code = -1
                log.mark_finished(code)
            threading.Thread(target=worker, daemon=True).start()

        WinetricksDialog(app=app, runtime=rt, on_run=on_run).present(self)

    def _run_winecfg(self, app):
        from .. import winetools
        from .log_window import LogWindow
        rt = self._runtime_for(app)
        if rt is None:
            self._toast(f"Runtime tidak ditemukan: {app.runtime}")
            return
        log = LogWindow(title=f"winecfg: {app.name}")
        log.present()

        def worker():
            try:
                code = winetools.run_winecfg(app, rt, on_output=log.append_line)
            except Exception as exc:
                log.append_line(f"[error] {exc}")
                code = -1
            log.mark_finished(code)
        threading.Thread(target=worker, daemon=True).start()

    # --- shortcut / remove ---
    def _launch_exec(self, app) -> str:
        import os
        appimage = os.environ.get("APPIMAGE")
        return f'"{appimage}" --run {app.id}' if appimage else f"agusemu --run {app.id}"

    def _make_shortcut(self, app):
        from .. import desktop
        desktop.create_shortcut(app, self._launch_exec(app), icon_src=app.icon or None)
        self._toast(f"Shortcut '{app.name}' dibuat")

    def _confirm_remove(self, app):
        dialog = Adw.AlertDialog(heading="Hapus aplikasi?",
                                 body=f"Hapus '{app.name}' dari library?")
        dialog.add_response("cancel", "Batal")
        dialog.add_response("remove", "Hapus")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(_d, resp):
            if resp == "remove":
                library.remove_app(app.id)
                if hasattr(self, "detail"):
                    del self.detail
                self.refresh_library()
                self._set_content_child(self._empty_state())
        dialog.connect("response", on_response)
        dialog.present(self)

    def _toast(self, text: str):
        self.toast_overlay.add_toast(Adw.Toast(title=text))

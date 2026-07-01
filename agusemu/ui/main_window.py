"""AgusEmu main window."""
from __future__ import annotations

import datetime as _dt
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import config, library  # noqa: E402
from ..models import App, make_app_id  # noqa: E402

LOGO_PATH = Path(__file__).parent / "assets" / "agusemu.png"
_CAT_LABEL = {"app": "Applications", "game": "Games"}


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("AgusEmu")
        self.set_default_size(960, 640)

        self.split = Adw.NavigationSplitView()

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("navigation-sidebar")
        self.listbox.set_header_func(self._header_func)
        self.listbox.connect("row-selected", self._on_row_selected)
        sidebar_scroll = Gtk.ScrolledWindow(child=self.listbox)
        sidebar_scroll.set_vexpand(True)

        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Add a ready-to-run app/game")
        add_btn.connect("clicked", lambda *_: self._open_add_dialog())
        install_btn = Gtk.Button(icon_name="system-software-install-symbolic")
        install_btn.set_tooltip_text("Install from an installer (.exe/.msi)")
        install_btn.connect("clicked", lambda *_: self._open_install_dialog())

        sidebar_page = Adw.NavigationPage(
            title="Library",
            child=self._chrome("Library", sidebar_scroll,
                               start_widgets=[add_btn, install_btn]))
        self.split.set_sidebar(sidebar_page)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.content_box.set_vexpand(True)
        self.content_box.append(self._empty_state())
        rt_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        rt_btn.set_tooltip_text("Runtime Manager")
        rt_btn.connect("clicked", self._open_runtime_manager)
        content_page = Adw.NavigationPage(
            title="AgusEmu",
            child=self._chrome("AgusEmu", self.content_box, end_widgets=[rt_btn]))
        self.split.set_content(content_page)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.split)
        self.set_content(self.toast_overlay)
        self.refresh_library()

    # --- layout helpers ---
    def _chrome(self, title, body, start_widgets=None, end_widgets=None):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        header = Adw.HeaderBar()
        for w in (start_widgets or []):
            header.pack_start(w)
        for w in (end_widgets or []):
            header.pack_end(w)
        box.append(header)
        body.set_vexpand(True)
        box.append(body)
        return box

    def _empty_state(self):
        page = Adw.StatusPage(
            title="AgusEmu",
            description="Add an app/game .exe, or install from an installer.")
        try:
            page.set_paintable(Gdk.Texture.new_from_filename(str(LOGO_PATH)))
        except Exception:
            page.set_icon_name("application-x-executable-symbolic")
        return page

    def _set_content_child(self, widget):
        child = self.content_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.content_box.remove(child)
            child = nxt
        self.content_box.append(widget)

    def _header_func(self, row, before):
        cat = getattr(row, "_category", "app")
        if before is not None and getattr(before, "_category", "app") == cat:
            row.set_header(None)
            return
        label = Gtk.Label(label=_CAT_LABEL.get(cat, "Applications"), xalign=0,
                          margin_top=10, margin_bottom=4, margin_start=12)
        label.add_css_class("heading")
        label.add_css_class("dim-label")
        row.set_header(label)

    def refresh_library(self):
        child = self.listbox.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.listbox.remove(child)
            child = nxt
        apps = library.load_apps()
        apps.sort(key=lambda a: (0 if a.category == "app" else 1, a.name.lower()))
        for app in apps:
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=app.name, xalign=0, margin_top=8,
                                    margin_bottom=8, margin_start=12, margin_end=12))
            row._app_id = app.id
            row._category = app.category
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

    # --- install from installer ---
    def _open_install_dialog(self):
        from .. import runtimes as rt_mod
        from .install_dialog import InstallDialog
        InstallDialog(runtimes=rt_mod.scan_runtimes(),
                      on_install=self._run_installer).present(self)

    def _run_installer(self, name, installer, category, runtime_name):
        from .. import launcher, runtimes as rt_mod
        from .log_window import LogWindow
        app_id = make_app_id(name)
        prefix = str(config.prefixes_dir() / app_id)
        log = LogWindow(title=f"Install: {name}")
        log.present()

        def worker():
            try:
                rt = rt_mod.ensure_runtime(runtime_name, on_status=log.append_line)
                tmp = App(id=app_id, name=name, exe_path=installer,
                          runtime=rt.name, prefix=prefix, category=category)
                log.append_line("Running installer…")
                code = launcher.launch(tmp, rt, on_output=log.append_line)
                log.mark_finished(code)
                GLib.idle_add(self._after_install, name, app_id, prefix,
                              rt.name, category)
            except Exception as exc:
                log.append_line(f"[error] {exc}")
                log.mark_finished(-1)

        threading.Thread(target=worker, daemon=True).start()

    def _after_install(self, name, app_id, prefix, runtime, category):
        """After the installer finishes, ask the user to pick the installed .exe."""
        dialog = Gtk.FileDialog(title="Pick the installed program (.exe)")
        drive_c = Path(prefix) / "pfx" / "drive_c"
        if drive_c.exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(drive_c)))
        filt = Gtk.FileFilter()
        filt.set_name("Windows program")
        filt.add_pattern("*.exe")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filt)
        dialog.set_filters(filters)

        def done(dlg, res):
            try:
                f = dlg.open_finish(res)
            except Exception:
                self._toast("Installation finished, but no program was selected.")
                return
            if not f:
                return
            app = App(id=app_id, name=name, exe_path=f.get_path(), runtime=runtime,
                      prefix=prefix, category=category,
                      created_at=_dt.date.today().isoformat())
            if library.get_app(app_id):
                library.update_app(app)
            else:
                library.add_app(app)
            self.refresh_library()
            self._toast(f"'{name}' added to the library")

        dialog.open(self, None, done)
        return False

    # --- runtime manager ---
    def _open_runtime_manager(self, *_):
        from .runtime_manager import RuntimeManager
        RuntimeManager().present(self)

    # --- launch (auto-download runtime if needed) ---
    def _launch_app(self, app):
        from .. import launcher, runtimes as rt_mod
        from .log_window import LogWindow
        log = LogWindow(title=f"Log: {app.name}")
        log.present()

        def worker():
            try:
                rt = rt_mod.ensure_runtime(app.runtime, on_status=log.append_line)
                if app.runtime != rt.name:
                    library.update_app(app.with_changes(runtime=rt.name))
                    GLib.idle_add(self.refresh_library)
                code = launcher.launch(app.with_changes(runtime=rt.name), rt,
                                       on_output=log.append_line)
            except Exception as exc:
                log.append_line(f"[error] {exc}")
                code = -1
            log.mark_finished(code)

        threading.Thread(target=worker, daemon=True).start()

    # --- winetricks / winecfg ---
    def _open_winetricks(self, app):
        from .. import runtimes as rt_mod, winetools
        from .log_window import LogWindow
        from .winetricks_dialog import WinetricksDialog

        def on_run(verbs):
            log = LogWindow(title=f"Winetricks: {app.name}")
            log.present()

            def worker():
                try:
                    rt = rt_mod.ensure_runtime(app.runtime, on_status=log.append_line)
                    code = winetools.run_winetricks(app.with_changes(runtime=rt.name),
                                                    rt, verbs, on_output=log.append_line)
                except Exception as exc:
                    log.append_line(f"[error] {exc}")
                    code = -1
                log.mark_finished(code)
            threading.Thread(target=worker, daemon=True).start()

        WinetricksDialog(app=app, runtime=None, on_run=on_run).present(self)

    def _run_winecfg(self, app):
        from .. import runtimes as rt_mod, winetools
        from .log_window import LogWindow
        log = LogWindow(title=f"winecfg: {app.name}")
        log.present()

        def worker():
            try:
                rt = rt_mod.ensure_runtime(app.runtime, on_status=log.append_line)
                code = winetools.run_winecfg(app.with_changes(runtime=rt.name), rt,
                                             on_output=log.append_line)
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
        icon = app.icon or (str(LOGO_PATH) if LOGO_PATH.exists() else None)
        desktop.create_shortcut(app, self._launch_exec(app), icon_src=icon)
        self._toast(f"Shortcut '{app.name}' created")

    def _confirm_remove(self, app):
        dialog = Adw.AlertDialog(heading="Remove application?",
                                 body=f"Remove '{app.name}' from the library?")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
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

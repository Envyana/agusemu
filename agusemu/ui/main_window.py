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
QR_PATH = Path(__file__).parent / "assets" / "support-qr.png"
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
        home_btn = Gtk.Button(icon_name="go-home-symbolic")
        home_btn.set_tooltip_text("Home")
        home_btn.connect("clicked", self._go_home)
        rt_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        rt_btn.set_tooltip_text("Runtime Manager")
        rt_btn.connect("clicked", self._open_runtime_manager)
        content_page = Adw.NavigationPage(
            title="AgusEmu",
            child=self._chrome("AgusEmu", self.content_box,
                               start_widgets=[home_btn], end_widgets=[rt_btn]))
        self.split.set_content(content_page)

        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self.split)
        self.set_content(self.toast_overlay)
        self._active_ops: set[str] = set()
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
            description="Add an app/game, or install from an installer (.exe/.msi).")
        try:
            page.set_paintable(Gdk.Texture.new_from_filename(str(LOGO_PATH)))
        except Exception:
            page.set_icon_name("application-x-executable-symbolic")
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                          halign=Gtk.Align.CENTER)
        add = Gtk.Button(label="Add app / game")
        add.add_css_class("pill")
        add.connect("clicked", lambda *_: self._open_add_dialog())
        install = Gtk.Button(label="Install from installer")
        install.add_css_class("pill")
        install.add_css_class("suggested-action")
        install.connect("clicked", lambda *_: self._open_install_dialog())
        buttons.append(add)
        buttons.append(install)
        page.set_child(buttons)
        page.set_vexpand(True)

        overlay = Gtk.Overlay()
        overlay.set_child(page)
        support = self._support_card()
        if support is not None:
            support.set_halign(Gtk.Align.END)
            support.set_valign(Gtk.Align.END)
            support.set_margin_end(16)
            support.set_margin_bottom(16)
            overlay.add_overlay(support)
        return overlay

    def _support_card(self):
        if not QR_PATH.exists():
            return None
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.add_css_class("card")
        label = Gtk.Label(label="Support me", margin_top=6,
                          margin_start=10, margin_end=10)
        label.add_css_class("caption-heading")
        label.add_css_class("accent")
        qr = Gtk.Picture.new_for_filename(str(QR_PATH))
        qr.set_size_request(96, 96)
        qr.set_content_fit(Gtk.ContentFit.CONTAIN)
        qr.set_margin_start(10)
        qr.set_margin_end(10)
        qr.set_margin_bottom(10)
        card.append(label)
        card.append(qr)
        return card

    def _set_content_child(self, widget):
        child = self.content_box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            self.content_box.remove(child)
            child = nxt
        self.content_box.append(widget)

    def _go_home(self, *_):
        self.listbox.unselect_all()
        self._set_content_child(self._empty_state())

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

    # --- generic logged runner (tailing window; flood-proof) ---
    def _run_logged(self, title, log_id, target):
        from .log_window import LogWindow
        if log_id in self._active_ops:
            # Klik ganda: jangan jalankan dua proses di prefix yang sama dan
            # jangan truncate log yang sedang di-tail jendela pertama.
            self._toast(f"'{title}' is already running")
            return
        self._active_ops.add(log_id)
        logpath = config.logs_dir() / f"{log_id}.log"
        open(logpath, "w").close()
        win = LogWindow(title=title)
        win.tail_file(str(logpath))
        win.present()

        def finish(code):
            self._active_ops.discard(log_id)
            # 3010 = ERROR_SUCCESS_REBOOT_REQUIRED dari msiexec: sukses.
            if code not in (0, 3010):
                self._toast(f"'{title}' failed (exit code {code}) — see log")
            return False

        def worker():
            code = -1
            try:
                with open(logpath, "a") as f:
                    def out(line):
                        f.write(line + "\n")
                        f.flush()
                    try:
                        code = target(out)
                    except Exception as exc:
                        out(f"[error] {exc}")
                        code = -1
                    out(f"\n[finished] exit code = {code}")
            finally:
                GLib.idle_add(finish, code)

        threading.Thread(target=worker, daemon=True).start()

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
        # Panel detail masih menampilkan (dan akan me-launch) data lama
        # jika tidak ikut disegarkan setelah edit.
        detail = getattr(self, "detail", None)
        if detail is not None and detail._app is not None \
                and detail._app.id == app.id:
            detail.show_app(app)

    # --- install from installer ---
    def _open_install_dialog(self):
        from .. import runtimes as rt_mod
        from .install_dialog import InstallDialog
        InstallDialog(runtimes=rt_mod.scan_runtimes(),
                      on_install=self._run_installer).present(self)

    def _run_installer(self, name, installer, category, runtime_name):
        from .. import launcher, runtimes as rt_mod
        app_id = make_app_id(name)
        prefix = str(config.prefixes_dir() / app_id)

        def target(out):
            rt = rt_mod.ensure_runtime(runtime_name, on_status=out)
            tmp = App(id=app_id, name=name, exe_path=installer,
                      runtime=rt.name, prefix=prefix, category=category)
            out("Running installer…")
            code = launcher.launch(tmp, rt, on_output=out)
            # Jangan minta pengguna memilih program terpasang jika
            # installer-nya sendiri gagal/dibatalkan.
            if code in (0, 3010):
                GLib.idle_add(self._after_install, name, app_id, prefix,
                              rt.name, category)
            else:
                out("[installer failed — nothing was added to the library]")
            return code

        self._run_logged(f"Install: {name}", app_id, target)

    def _after_install(self, name, app_id, prefix, runtime, category):
        dialog = Gtk.FileDialog(title="Pick the installed program (.exe)")
        base = Path(prefix) / "pfx" / "drive_c"
        for candidate in ("Program Files", "Program Files (x86)"):
            pf = base / candidate
            if pf.exists():
                base = pf
                break
        if base.exists():
            dialog.set_initial_folder(Gio.File.new_for_path(str(base)))
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

    # --- launch (shows a tailing log window: download progress + run output) ---
    def _launch_app(self, app):
        from .. import launcher, runtimes as rt_mod

        def target(out):
            rt = rt_mod.ensure_runtime(app.runtime, on_status=out)
            if app.runtime != rt.name:
                # set_runtime hanya menyentuh field runtime pada rekaman
                # terkini — editan pengguna selama unduhan tidak tertimpa
                # snapshot `app` yang basi.
                library.set_runtime(app.id, rt.name)
                GLib.idle_add(self.refresh_library)
            return launcher.launch(app.with_changes(runtime=rt.name), rt, on_output=out)

        self._run_logged(f"Log: {app.name}", app.id, target)

    # --- winetricks / winecfg ---
    def _open_winetricks(self, app):
        from .. import runtimes as rt_mod, winetools
        from .winetricks_dialog import WinetricksDialog

        def on_run(verbs):
            def target(out):
                rt = rt_mod.ensure_runtime(app.runtime, on_status=out)
                return winetools.run_winetricks(app.with_changes(runtime=rt.name),
                                                rt, verbs, on_output=out)
            self._run_logged(f"Winetricks: {app.name}", app.id + "-winetricks", target)

        WinetricksDialog(app=app, runtime=None, on_run=on_run).present(self)

    def _run_winecfg(self, app):
        from .. import runtimes as rt_mod, winetools

        def target(out):
            rt = rt_mod.ensure_runtime(app.runtime, on_status=out)
            return winetools.run_winecfg(app.with_changes(runtime=rt.name), rt,
                                         on_output=out)

        self._run_logged(f"winecfg: {app.name}", app.id + "-winecfg", target)

    # --- shortcut / remove ---
    def _launch_exec(self, app) -> str:
        import os
        appimage = os.environ.get("APPIMAGE")
        return f'"{appimage}" --run {app.id}' if appimage else f"agusemu --run {app.id}"

    def _make_shortcut(self, app):
        from .. import desktop, icons
        launch_exec = self._launch_exec(app)

        # Ekstraksi ikon membaca & mem-parse seluruh .exe — pada game
        # berukuran GB hal ini membekukan UI jika dikerjakan di main thread.
        def worker():
            try:
                icon = icons.extract_exe_icon(
                    app.exe_path, config.icons_dir() / f"{app.id}-exe.png")
                icon_src = str(icon) if icon else (
                    app.icon or (str(LOGO_PATH) if LOGO_PATH.exists() else None))
                desktop.create_shortcut(app, launch_exec, icon_src=icon_src)
            except OSError as exc:
                GLib.idle_add(self._toast, f"Failed to create shortcut: {exc}")
                return
            GLib.idle_add(self._toast, f"Shortcut '{app.name}' created")

        threading.Thread(target=worker, daemon=True).start()

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

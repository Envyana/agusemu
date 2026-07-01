"""Dialog manajer runtime GE-Proton."""
from __future__ import annotations

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402

from .. import config, runtimes  # noqa: E402


class RuntimeManager(Adw.Dialog):
    def __init__(self):
        super().__init__()
        self.set_title("Manajer Runtime")
        self.set_content_width(560)
        self.set_content_height(560)
        self._installed_rows = []

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        add_folder = Gtk.Button(label="Tambah folder…")
        add_folder.connect("clicked", self._on_add_folder)
        header.pack_start(add_folder)
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.installed_group = Adw.PreferencesGroup(title="Terpasang")
        box.append(self.installed_group)
        self.available_group = Adw.PreferencesGroup(title="Tersedia untuk diunduh")
        load = Gtk.Button(label="Muat daftar rilis", valign=Gtk.Align.CENTER)
        load.connect("clicked", self._on_load_releases)
        self.available_group.set_header_suffix(load)
        box.append(self.available_group)

        scroll = Gtk.ScrolledWindow(child=box)
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)
        self.set_child(toolbar)
        self._refresh_installed()

    def _refresh_installed(self):
        for row in self._installed_rows:
            self.installed_group.remove(row)
        self._installed_rows = []
        for rt in runtimes.scan_runtimes():
            row = Adw.ActionRow(title=rt.name, subtitle=rt.source)
            self.installed_group.add(row)
            self._installed_rows.append(row)
        return False

    def _on_add_folder(self, _btn):
        dialog = Gtk.FileDialog(title="Pilih folder runtime")

        def done(dlg, res):
            try:
                folder = dlg.select_folder_finish(res)
            except Exception:
                return
            if folder:
                cfg = config.load_config()
                dirs = list(cfg.get("extra_runtime_dirs", []))
                if folder.get_path() not in dirs:
                    dirs.append(folder.get_path())
                cfg["extra_runtime_dirs"] = dirs
                config.save_config(cfg)
                self._refresh_installed()

        dialog.select_folder(self.get_root(), None, done)

    def _on_load_releases(self, _btn):
        def worker():
            try:
                rels = runtimes.fetch_releases(limit=15)
            except Exception as exc:
                GLib.idle_add(self._add_available_error, str(exc))
                return
            GLib.idle_add(self._populate_releases, rels)
        threading.Thread(target=worker, daemon=True).start()

    def _add_available_error(self, msg):
        self.available_group.add(Adw.ActionRow(title="Gagal memuat", subtitle=msg))
        return False

    def _populate_releases(self, rels):
        installed = {r.name for r in runtimes.scan_runtimes()}
        for rel in rels:
            row = Adw.ActionRow(title=rel.tag)
            if rel.tag in installed:
                row.set_subtitle("Sudah terpasang")
            else:
                btn = Gtk.Button(label="Unduh", valign=Gtk.Align.CENTER)
                btn.connect("clicked", self._on_download, rel, row)
                row.add_suffix(btn)
            self.available_group.add(row)
        return False

    def _on_download(self, btn, rel, row):
        btn.set_sensitive(False)
        progress = Gtk.ProgressBar(valign=Gtk.Align.CENTER, hexpand=True)
        row.add_suffix(progress)

        def on_progress(done, total):
            GLib.idle_add(progress.set_fraction, (done / total) if total else 0.0)

        def worker():
            try:
                runtimes.download_runtime(rel, progress=on_progress)
                GLib.idle_add(row.set_subtitle, "Selesai diunduh")
            except Exception as exc:
                GLib.idle_add(row.set_subtitle, f"Gagal: {exc}")
            GLib.idle_add(self._refresh_installed)

        threading.Thread(target=worker, daemon=True).start()

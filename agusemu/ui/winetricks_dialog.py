"""Winetricks verb picker dialog."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

PRESETS = ["corefonts", "vcrun2019", "dotnet48", "d3dcompiler_47", "dxvk"]


class WinetricksDialog(Adw.Dialog):
    def __init__(self, app, runtime, on_run):
        super().__init__()
        self._on_run = on_run
        self.set_title("Winetricks / Components")
        self.set_content_width(460)

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        run = Gtk.Button(label="Run")
        run.add_css_class("suggested-action")
        run.connect("clicked", self._on_run_clicked)
        header.pack_end(run)
        toolbar.add_top_bar(header)

        group = Adw.PreferencesGroup(title="Common components", margin_top=12,
                                     margin_bottom=12, margin_start=12, margin_end=12)
        self._switches = {}
        for verb in PRESETS:
            row = Adw.SwitchRow(title=verb)
            group.add(row)
            self._switches[verb] = row
        self.custom = Adw.EntryRow(title="Extra verbs (space-separated)")
        group.add(self.custom)

        toolbar.set_content(group)
        self.set_child(toolbar)

    def _collect_verbs(self):
        verbs = [v for v, row in self._switches.items() if row.get_active()]
        return verbs + self.custom.get_text().split()

    def _on_run_clicked(self, _btn):
        verbs = self._collect_verbs()
        if verbs:
            self._on_run(verbs)
        self.close()

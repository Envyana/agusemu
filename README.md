# AgusEmu

**Run Windows `.exe` / `.msi` apps and games on Linux — powered by GE-Proton via [umu-launcher](https://github.com/Open-Wine-Components/umu-launcher).**

AgusEmu is a small, focused GTK4 / libadwaita desktop app that lets you install
and launch Windows programs and games on Linux without touching the terminal.
Each app gets its own isolated Wine prefix, and GE-Proton runtimes are
downloaded automatically on first launch.

> Think of it as a lightweight, friendly launcher for Windows software on
> Linux — pick a runtime, add your `.exe`, hit **Launch**.

---

## Features

- 🎮 **Games & everyday apps** — organized into two categories in the sidebar.
- 📦 **Install from installers** — run a Windows `.exe`/`.msi` installer, then
  pick the installed program; it lands in your library ready to launch.
- 🧩 **Per-app prefixes** — every app has its own isolated `C:` drive, so one
  broken app never affects the others.
- ⚙️ **Automatic GE-Proton** — if no runtime is present, the latest GE-Proton is
  downloaded automatically the first time you launch. You can also point AgusEmu
  at GE-Proton folders you already have, or download specific versions from the
  Runtime Manager.
- 🍷 **Winetricks & winecfg** — install common components (corefonts, vcrun,
  dotnet, …) and tweak each prefix from the UI.
- 🎛️ **DXVK/VKD3D toggle & custom env vars** per app.
- 🔗 **Menu shortcuts** — create a `.desktop` launcher, using the program's own
  icon extracted from its `.exe` when possible.
- 📥 **Self-contained AppImage** — bundles `umu-run`; relies on your system's
  GTK4/libadwaita.

## Install

### AppImage (recommended)

Download `AgusEmu-x86_64.AppImage` from the
[Releases](../../releases) page, then:

```bash
chmod +x AgusEmu-x86_64.AppImage
./AgusEmu-x86_64.AppImage
```

On first run it installs a desktop launcher (with icon) into your app menu.

**Requirements:** a modern Linux distro with **GTK4 + libadwaita** installed
(present on most current distros, e.g. Ubuntu 24.04+/Fedora). `umu-run` is
bundled inside the AppImage.

### From source

```bash
git clone <this-repo>
cd agusemu
python3 -m pytest        # optional: run the test suite
python3 -m agusemu.main  # launch the GUI
```

Source runs need **PyGObject (GTK4 + libadwaita)** and the **`umu-run`** binary
on `PATH` (or set `AGUSEMU_UMU_RUN=/path/to/umu-run`). Get umu-launcher from its
[releases](https://github.com/Open-Wine-Components/umu-launcher/releases).

## Usage

1. **Home screen** → **Add app / game** (for a ready-to-run `.exe`) or
   **Install from installer** (for an `.exe`/`.msi` setup).
2. Pick the file, give it a name, choose a category and a runtime
   (**Automatic** downloads the latest GE-Proton).
3. Select the entry in the sidebar → **Launch**.
4. Use **Winetricks / Components**, **Open winecfg**, **Create Menu Shortcut**,
   **Edit**, or **Remove** from the detail panel. The **Home** button returns to
   the start screen.

### Where are my files?

Everything lives under `~/.local/share/AgusEmu/`:

```
AgusEmu/
├── runtimes/          # downloaded GE-Proton versions
├── prefixes/<app>/    # per-app Wine prefix (its C: drive is pfx/drive_c)
├── logs/<app>.log     # per-app run logs
├── library.json       # your apps
└── config.json        # settings
```

Inside a running Windows app, your Linux filesystem is available at the **`Z:`**
drive (via *File → Open*).

## How it works

AgusEmu builds the environment (`GAMEID`, `PROTONPATH`, `WINEPREFIX`, …) and runs
your program through `umu-run`, which sets up the Steam Linux Runtime container
and GE-Proton outside of Steam. Windows installers (`.msi`) are run via
`msiexec /i`.

## Build the AppImage

```bash
bash packaging/build-appimage.sh
```

Produces `AgusEmu-x86_64.AppImage`. It downloads the official `umu-run` zipapp
and bundles it; GTK4/libadwaita is taken from the host system.

## Tech stack

Python 3 · PyGObject (GTK4 + libadwaita) · umu-launcher · GE-Proton · pytest.
Core logic is GTK-free and unit-tested; the GUI layer is a thin shell on top.

## Known limitations

- **Drag-and-drop from the Linux file manager into a Wine window is unreliable**
  and can make the *Windows app* hang — this is a Wine/Proton limitation shared
  by all Wine-based launchers. Use the app's *File → Open* (drive `Z:`) instead.
- The AppImage relies on system GTK4/libadwaita rather than bundling it.

## License

[GPL-3.0-or-later](LICENSE). © AgusEmu contributors.

## Credits

Built on the excellent work of
[umu-launcher](https://github.com/Open-Wine-Components/umu-launcher) and
[GE-Proton](https://github.com/GloriousEggroll/proton-ge-custom).

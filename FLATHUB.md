# Publishing AgusEmu on Flathub

This repo ships everything Flathub needs under `flatpak/`:

- `com.patopo.AgusEmu.yaml` — Flatpak manifest
- `com.patopo.AgusEmu.metainfo.xml` — AppStream metadata
- `com.patopo.AgusEmu.desktop` — desktop entry
- `com.patopo.AgusEmu.png` — icon
- `agusemu-launcher.sh` — in-sandbox entry point

## 0. Prerequisites

The app ID is **`com.patopo.AgusEmu`**. Flathub requires the ID to match a
domain/host you control:

- **You own `patopo.com`** → keep this ID and complete Flathub's website
  verification for the domain (add the token file / DNS record Flathub gives you).
- **You do NOT own it** → rename everywhere to **`io.github.Envyana.AgusEmu`**
  (manifest app-id, metainfo `<id>`, desktop filename, icon filename, and the
  `application_id` in `agusemu/main.py` + `agusemu/integrate.py`). `io.github.*`
  needs no domain verification because the repo is on GitHub.

## 1. Build & test locally first

```bash
flatpak install -y flathub org.gnome.Platform//48 org.gnome.Sdk//48
flatpak-builder --user --install --force-clean build-dir flatpak/com.patopo.AgusEmu.yaml
flatpak run com.patopo.AgusEmu
```

Fix anything that fails here before submitting. **The hard part is running
GE-Proton (Steam Linux Runtime / pressure-vessel) inside the Flatpak sandbox** —
expect to iterate on `finish-args` (this is normal; Steam and Heroic solved the
same problem).

## 2. Add screenshots

Flathub requires at least one working screenshot. Add PNGs under
`flatpak/screenshots/` and make sure the URL(s) in `com.patopo.AgusEmu.metainfo.xml`
resolve (they point at `raw.githubusercontent.com/.../main/flatpak/screenshots/`).
Validate metadata:

```bash
flatpak run org.flatpak.Builder --version   # or: flatpak-builder-lint
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest flatpak/com.patopo.AgusEmu.yaml
flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream flatpak/com.patopo.AgusEmu.metainfo.xml
```

## 3. Submit to Flathub

1. Fork **https://github.com/flathub/flathub**.
2. Create a branch **named exactly `com.patopo.AgusEmu`**.
3. Put the manifest (and any local files it references) at the repo root of that
   branch.
4. Open a Pull Request against `flathub/flathub`. A bot builds it; maintainers
   review. Respond to feedback and iterate.
5. Once merged, Flathub creates a dedicated repo `flathub/com.patopo.AgusEmu`
   and grants you commit access. Future updates = PRs there (bump the `commit:`
   in the manifest and the `<release>` in metainfo).

See the official guide: https://docs.flathub.org/docs/for-app-authors/submission

## 4. Updating releases later

- Tag a new version in this repo, update `commit:` in the manifest and add a
  `<release>` entry in the metainfo, then PR it to your `flathub/` app repo.

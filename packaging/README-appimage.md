# Build AppImage AgusEmu

    bash packaging/build-appimage.sh

Menghasilkan `AgusEmu-x86_64.AppImage`.

## Catatan
- v1 mengandalkan GTK4 + libadwaita **sistem** (tersedia di mayoritas distro
  modern). Bila target tidak punya, pasang paket GTK4/libadwaita distro.
- `umu-run` dibundel; GE-Proton diunduh oleh aplikasi saat runtime ke
  direktori data pengguna.
- Peningkatan lanjutan: membundel penuh GTK4/libadwaita agar mandiri total.

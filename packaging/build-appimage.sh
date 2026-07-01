#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$HERE/build/appimage"
APPDIR="$BUILD/AgusEmu.AppDir"
UMU_URL="${UMU_URL:-https://github.com/Open-Wine-Components/umu-launcher/releases/latest/download/umu-run}"

rm -rf "$BUILD"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib/agusemu" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# 1) Salin paket agusemu (termasuk aset ikon di agusemu/ui/assets)
cp -r "$HERE/agusemu" "$APPDIR/usr/lib/agusemu/agusemu"

# 2) Ambil umu-run (zipapp mandiri) dan jadikan executable
curl -L "$UMU_URL" -o "$APPDIR/usr/bin/umu-run"
chmod +x "$APPDIR/usr/bin/umu-run"

# 3) desktop + ikon (PNG logo AE)
cp "$HERE/packaging/AgusEmu.desktop" "$APPDIR/usr/share/applications/"
cp "$HERE/packaging/AgusEmu.desktop" "$APPDIR/AgusEmu.desktop"
cp "$HERE/packaging/agusemu-256.png" \
   "$APPDIR/usr/share/icons/hicolor/256x256/apps/agusemu.png"
cp "$HERE/packaging/agusemu.png" "$APPDIR/agusemu.png"

# 4) AppRun
cat > "$APPDIR/AppRun" <<'RUNEOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
export PYTHONPATH="$HERE/usr/lib/agusemu:${PYTHONPATH:-}"
export AGUSEMU_UMU_RUN="$HERE/usr/bin/umu-run"
exec python3 -m agusemu.main "$@"
RUNEOF
chmod +x "$APPDIR/AppRun"

# 5) Bungkus dengan appimagetool
if ! command -v appimagetool >/dev/null 2>&1; then
  curl -L "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
    -o "$BUILD/appimagetool"
  chmod +x "$BUILD/appimagetool"
  APPIMAGETOOL="$BUILD/appimagetool"
else
  APPIMAGETOOL="appimagetool"
fi
ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$HERE/AgusEmu-x86_64.AppImage"
echo "Selesai: $HERE/AgusEmu-x86_64.AppImage"

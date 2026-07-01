# AgusEmu — Design Spec

**Tanggal:** 2026-07-01
**Status:** Disetujui (siap masuk tahap perencanaan implementasi)

## 1. Tujuan

AgusEmu adalah aplikasi desktop Linux untuk menjalankan file `.exe` Windows
(game maupun aplikasi umum) menggunakan **GE-Proton** sebagai runtime, dijalankan
di luar Steam melalui **umu-launcher**. Pengguna memilih versi GE-Proton yang
sudah di-download (atau mengunduhnya dari dalam aplikasi), lalu menambahkan
aplikasi/game ke library dan menjalankannya dengan satu klik.

Target akhir: dikemas menjadi **AppImage** agar berjalan di semua distro.

## 2. Lingkungan Target

- Ubuntu 26.04 (dan distro Linux modern lain), GNOME/Wayland sebagai acuan.
- Python 3.14, PyGObject/GTK4, libadwaita.
- Engine: umu-launcher (`umu-run`).
- Runtime: GE-Proton (rilis dari GloriousEggroll/proton-ge-custom).

## 3. Konsep Inti

- **Runtime** — sebuah versi GE-Proton (folder berisi `proton` + toolkit).
  Bisa di-scan dari folder lokal atau di-download dari GitHub.
- **App/Game** — satu entri library: nama, path `.exe`, ikon, runtime terpilih,
  prefix sendiri, argumen, env vars kustom, toggle DXVK/VKD3D.
- **Prefix per aplikasi** — tiap entri memiliki drive C: virtual terpisah
  (isolasi penuh; kerusakan satu app tidak memengaruhi yang lain).

## 4. Struktur Data

Lokasi data mengikuti XDG (`$XDG_DATA_HOME` atau `~/.local/share/AgusEmu/`):

```
AgusEmu/
├── runtimes/            # GE-Proton-9-x, GE-Proton-10-x, ...
├── prefixes/<app-id>/   # STEAM_COMPAT_DATA_PATH per app (berisi pfx/)
├── library.json         # daftar app + konfigurasinya
└── config.json          # setting global (folder runtime tambahan, dll)
```

- `app-id` = slug unik (mis. dari nama + hash pendek) untuk memetakan prefix.
- `config.json` menyimpan daftar folder runtime eksternal yang diarahkan user.

### Skema `library.json`
Objek dengan kunci `apps` berisi array entri:
```
{ "id", "name", "exe_path", "icon", "runtime", "prefix",
  "args", "env" (map string→string), "dxvk_enabled" (bool),
  "created_at" (YYYY-MM-DD) }
```

### Skema `config.json`
```
{ "extra_runtime_dirs": [string], "default_runtime": string|null }
```

## 5. Arsitektur Modul

Prinsip: banyak file kecil, fokus, batas antar-modul jelas, data immutable.

| Modul | Tanggung jawab | Bergantung pada |
|---|---|---|
| `config.py` | Path XDG, load/save `config.json`, konstanta | — |
| `models.py` | Dataclass `App`, `Runtime` (frozen/immutable) | — |
| `library.py` | CRUD `library.json` (add/update/remove/list) | config, models |
| `runtimes.py` | Scan runtime lokal, ambil daftar rilis GitHub, download+ekstrak GE-Proton (progress + verifikasi sha512) | config, models |
| `launcher.py` | Susun ENV + jalankan `umu-run`, stream stdout/stderr | config, models |
| `winetools.py` | winetricks, winecfg, toggle DXVK/VKD3D — semua via `umu-run` | launcher |
| `desktop.py` | Buat `.desktop` + ikon di menu aplikasi GNOME | config, models |
| `deps.py` | Cek ketersediaan `umu-run`/winetricks (dibundel di AppImage) | — |
| `ui/` | Jendela utama (sidebar library + panel detail), dialog tambah app, manajer runtime, setting, jendela log | semua di atas |
| `main.py` | Entry `Adw.Application` | ui |

## 6. Cara Menjalankan (Engine)

`umu-run` dipanggil sebagai subprocess dengan environment:

```
GAMEID=0
PROTONPATH=<folder GE-Proton terpilih>
STEAM_COMPAT_DATA_PATH=<prefixes/app-id>   # umu turunkan WINEPREFIX dari sini
WINEPREFIX=<prefixes/app-id>/pfx           # bila diperlukan langsung
+ env kustom user:
    - Toggle DXVK OFF → PROTON_USE_WINED3D=1
    - DXVK_HUD, VKD3D_CONFIG, dsb sesuai input user
→ umu-run "<path app.exe>" <args user>
```

- **winetricks**: `umu-run winetricks <verb>` dengan ENV yang sama.
- **winecfg**: `umu-run winecfg`.
- Semua operasi terhadap prefix memakai runtime yang sama demi konsistensi.

## 7. Alur Data

1. **Tambah app**: user pilih `.exe`, isi nama, pilih runtime → dibuat `app-id`
   + folder prefix → disimpan ke `library.json`.
2. **Launch**: `launcher` menyusun ENV dari konfigurasi app + path runtime →
   spawn `umu-run` → stdout/stderr distream ke jendela log secara real-time.
3. **Manajer runtime**: tampilkan runtime terpasang + daftar rilis GitHub →
   user pilih versi → download `.tar.gz` → verifikasi checksum → ekstrak ke
   `runtimes/`.
4. **Shortcut**: `desktop.py` menghasilkan file `.desktop` yang memanggil
   AgusEmu untuk menjalankan app tertentu, plus menyalin ikon.

## 8. Penanganan Error

- Validasi `.exe` dan runtime ada sebelum launch; pesan jelas bila tidak.
- Download gagal → retry + verifikasi checksum sha512 (disediakan rilis GE).
- Runtime crash → exit code non-zero ditampilkan; log lengkap tersedia.
- `umu-run` tidak ditemukan → di dev: instruksi instalasi; di AppImage: dibundel.
- Tidak ada error yang ditelan diam-diam; semua kegagalan tampil di UI + log.

## 9. Pengemasan AppImage (Fase Akhir)

- AppDir berisi Python relokatable + GTK4/libadwaita + umu-launcher, lalu
  `appimagetool`.
- **Catatan risiko:** membundel GTK4+libadwaita ke AppImage berat dan paling
  rumit. Dijadikan fase terakhir setelah aplikasi berjalan sempurna secara lokal.
- **Opsi cadangan** bila terlalu berat: AppImage mengandalkan GTK4 sistem
  (tersedia di mayoritas distro modern), hanya membundel kode AgusEmu + umu.

## 10. Testing

- **Unit test**: CRUD library, parsing versi runtime, parsing rilis GitHub
  (mock HTTP), penyusunan ENV launch, pembuatan app-id/slug.
- **Integrasi manual**: menjalankan satu `.exe` nyata dengan GE-Proton yang
  di-download; verifikasi prefix terbentuk dan aplikasi tampil.

## 11. Fitur v1 (disepakati)

- Manajemen runtime GE-Proton (download in-app + arahkan folder).
- Library app/game dengan prefix terpisah per app.
- Launch via umu-run + jendela log real-time.
- Winetricks & komponen Windows per prefix.
- Toggle DXVK/VKD3D + env vars kustom per app.
- Shortcut `.desktop` ke menu aplikasi GNOME.
- winecfg per prefix.

## 12. Urutan Pembangunan

1. Core: `config`, `models`, `library`, scan runtime, `launcher` (+ CLI kecil untuk uji).
2. Download GE-Proton dari GitHub (rilis + checksum).
3. GUI GTK4: library, tambah app, launch, jendela log.
4. Manajer runtime di GUI + winetricks/winecfg/toggle DXVK + shortcut `.desktop`.
5. Pengemasan AppImage.

## Non-Goals (v1)

- Bukan pengganti penuh Lutris/Bottles (tanpa integrasi toko game, tanpa
  manajemen cloud save).
- Tanpa auto-update runtime terjadwal.
- Tanpa dukungan Windows game store DRM khusus di luar kemampuan GE-Proton.

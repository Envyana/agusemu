# AgusEmu

Aplikasi desktop Linux untuk menjalankan file `.exe` Windows (game & aplikasi)
menggunakan GE-Proton via umu-launcher, dengan prefix terpisah per aplikasi.

## Pengembangan

    python3 -m venv --system-site-packages .venv
    . .venv/bin/activate
    pip install -e ".[dev]"
    python3 -m pytest

Lihat `docs/superpowers/` untuk spec & rencana.

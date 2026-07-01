#!/bin/sh
# AgusEmu entry point inside the Flatpak sandbox.
export PYTHONPATH="/app/lib/agusemu:${PYTHONPATH}"
export AGUSEMU_UMU_RUN="/app/bin/umu-run"
exec python3 -m agusemu.main "$@"

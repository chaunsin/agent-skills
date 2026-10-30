#!/usr/bin/env bash
# Compatibility entry point for the local, checksum-verified installer.
set -euo pipefail
exec python3 "$(dirname "$0")/install.py" "$@"

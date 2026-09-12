#!/usr/bin/env bash
# LoopForge - Linux Uninstaller
set -e

INSTALL_DIR="$HOME/.local/share/loopforge"
BIN_LINK="$HOME/.local/bin/loopforge"

echo ""
echo "Menghapus LoopForge dari Linux..."

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "  ✓ Folder $INSTALL_DIR dihapus"
else
    echo "  - Folder $INSTALL_DIR tidak ditemukan (skip)"
fi

if [ -f "$BIN_LINK" ]; then
    rm -f "$BIN_LINK"
    echo "  ✓ Command loopforge dihapus"
else
    echo "  - Command loopforge tidak ditemukan (skip)"
fi

echo ""
echo "✓ LoopForge berhasil dihapus dari Linux!"
echo ""

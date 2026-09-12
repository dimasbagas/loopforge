#!/data/data/com.termux/files/usr/bin/bash
# LoopForge - Termux Uninstaller
set -e

INSTALL_DIR="$PREFIX/opt/loopforge"
BIN_LINK="$PREFIX/bin/loopforge"

echo ""
echo "Menghapus LoopForge..."

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
echo "✓ LoopForge berhasil dihapus dari Termux!"
echo ""

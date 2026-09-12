#!/usr/bin/env bash
# LoopForge - Linux Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-linux.sh | bash
set -e

REPO_URL="https://github.com/dimasbagas/loopforge.git"
INSTALL_DIR="$HOME/.local/share/loopforge"
BIN_DIR="$HOME/.local/bin"
BIN_LINK="$BIN_DIR/loopforge"

echo ""
echo "=============================================="
echo "    _                    ___                  "
echo "   | |    ___   ___  _ _| __| ___  _ _ __ ___ "
echo "   | |__ / _ \ / _ \| '_ \ _/ _ \| '_/ _' / -_)"
echo "   |____|\___/ \___/| .__/_|\___/|_| \__, \___|"
echo "                    |_|               |___/    "
echo ""
echo "        LoopForge Linux Installer v1.0.0       "
echo "=============================================="
echo ""

# ─── Step 1: Check Python & Git & FFmpeg ──────────
echo "[1/5] Memeriksa dependensi sistem..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 belum terinstall!"
    echo "       Install terlebih dahulu (contoh: sudo apt install python3 python3-pip python3-venv)"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "ERROR: git belum terinstall!"
    echo "       Install terlebih dahulu (contoh: sudo apt install git)"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: ffmpeg belum terinstall!"
    echo "         Silakan install ffmpeg (contoh: sudo apt install ffmpeg atau sudo pacman -S ffmpeg)"
fi

# ─── Step 2: Clone/Update repository ──────────────
echo "[2/5] Mengambil LoopForge dari GitHub..."
if [ -d "$INSTALL_DIR" ]; then
    echo "      Menghapus instalasi lama..."
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$(dirname "$INSTALL_DIR")"
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

# ─── Step 3: Create virtual environment ───────────
echo "[3/5] Membuat virtual environment & menginstall dependency..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip --quiet
"$INSTALL_DIR/.venv/bin/pip" install -e "$INSTALL_DIR" --quiet

# ─── Step 4: Create launcher ──────────────────────
echo "[4/5] Membuat command 'loopforge' di $BIN_LINK..."
mkdir -p "$BIN_DIR"
cat > "$BIN_LINK" <<EOF
#!/usr/bin/env bash
exec "$INSTALL_DIR/.venv/bin/loopforge" "\$@"
EOF
chmod +x "$BIN_LINK"

# ─── Step 5: Check PATH ────────────────────────────
echo "[5/5] Memeriksa PATH..."
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  ⚠️  PERHATIAN: Folder $BIN_DIR belum ada di PATH Anda."
    echo "      Tambahkan baris berikut ke ~/.bashrc atau ~/.zshrc:"
    echo '      export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "=============================================="
echo "     ✓ INSTALASI LOOPFORGE SELESAI!          "
echo "=============================================="
echo ""
echo "  Cara memulai:"
echo "    loopforge              # Interactive wizard"
echo "    loopforge --version    # Cek versi"
echo ""
echo "  Uninstall:"
echo "    curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/uninstall-linux.sh | bash"
echo ""

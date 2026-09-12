#!/data/data/com.termux/files/usr/bin/bash
# LoopForge - Termux/Android Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-termux.sh | bash
set -e

REPO_URL="https://github.com/dimasbagas/loopforge.git"
INSTALL_DIR="$PREFIX/opt/loopforge"
BIN_LINK="$PREFIX/bin/loopforge"

# ─── Banner ────────────────────────────────────────
echo ""
echo "=============================================="
echo "    _                    ___                  "
echo "   | |    ___   ___  _ _| __| ___  _ _ __ ___ "
echo "   | |__ / _ \ / _ \| '_ \ _/ _ \| '_/ _' / -_)"
echo "   |____|\___/ \___/| .__/_|\___/|_| \__, \___|"
echo "                    |_|               |___/    "
echo ""
echo "       LoopForge Termux Installer v1.0.0       "
echo "=============================================="
echo ""

# ─── Step 1: Install system packages ──────────────
echo "[1/6] Mengupdate dan menginstall paket sistem..."
pkg update -y
pkg install -y python ffmpeg git curl

# ─── Step 2: Check Python version ─────────────────
echo "[2/6] Memeriksa versi Python..."
PY_VER="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "      Python: $PY_VER"

python - <<'PY'
import sys
if sys.version_info < (3, 12):
    print("ERROR: LoopForge membutuhkan Python 3.12+")
    print(f"       Versi saat ini: {sys.version}")
    raise SystemExit(1)
print("      Versi Python OK!")
PY

# ─── Step 3: Check FFmpeg ─────────────────────────
echo "[3/6] Memeriksa FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1)
    echo "      $FFMPEG_VER"
else
    echo "ERROR: FFmpeg tidak ditemukan!"
    exit 1
fi

# ─── Step 4: Clone/Update repository ──────────────
echo "[4/6] Mengambil LoopForge dari GitHub..."
if [ -d "$INSTALL_DIR" ]; then
    echo "      Menghapus instalasi lama..."
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$(dirname "$INSTALL_DIR")"
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

# ─── Step 5: Install Python dependencies ──────────
echo "[5/6] Menginstall dependency Python..."
python -m pip install --upgrade pip 2>/dev/null || true
python -m pip install \
  "typer>=0.12.0" \
  "rich>=13.7.0" \
  "pydantic>=2.5.0" \
  "yt-dlp>=2024.7.0"

# Buat folder kerja
mkdir -p "$INSTALL_DIR/outputs" "$INSTALL_DIR/downloads" "$INSTALL_DIR/logs"

# ─── Step 6: Create loopforge command ──────────────
echo "[6/6] Membuat command 'loopforge'..."
cat > "$BIN_LINK" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$INSTALL_DIR"
exec python "$INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$BIN_LINK"

# ─── Done ──────────────────────────────────────────
echo ""
echo "=============================================="
echo "     ✓ INSTALASI LOOPFORGE SELESAI!          "
echo "=============================================="
echo ""
echo "  Cara memulai:"
echo "    loopforge              # Interactive wizard"
echo "    loopforge --version    # Cek versi"
echo ""
echo "  Contoh penggunaan:"
echo "    loopforge local /sdcard/Movies/video.mp4 -d 1h"
echo "    loopforge youtube 'URL_YOUTUBE' -d 8h"
echo ""
echo "  Output tersimpan di:"
echo "    $INSTALL_DIR/outputs/"
echo ""
echo "  Akses penyimpanan Android:"
echo "    termux-setup-storage"
echo ""
echo "  Uninstall:"
echo "    curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/uninstall-termux.sh | bash"
echo ""

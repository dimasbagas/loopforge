#!/data/data/com.termux/files/usr/bin/bash
set -e

REPO_URL="https://github.com/dimasbagas/loopforge.git"
INSTALL_DIR="$PREFIX/opt/loopforge"
BIN="$PREFIX/bin/loopforge"

echo "=============================================="
echo "        LoopForge - Termux Installer"
echo "=============================================="
echo

echo "[1/5] Memeriksa Python..."
pkg update -y
pkg install -y python ffmpeg git curl

PY_VER="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "      Python: $PY_VER"

python - <<'PY'
import sys
if sys.version_info < (3, 12):
    raise SystemExit("LoopForge membutuhkan Python 3.12 atau lebih baru.")
PY

echo "[2/5] Mengambil LoopForge..."
rm -rf "$INSTALL_DIR"
mkdir -p "$(dirname "$INSTALL_DIR")"
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

echo "[3/5] Memasang dependency Python Termux..."
python -m pip install --upgrade pip
python -m pip install \
  "typer>=0.12.0" \
  "rich>=13.7.0" \
  "pydantic>=2.5.0" \
  "yt-dlp>=2024.7.0"

echo "[4/5] Membuat folder kerja..."
mkdir -p "$INSTALL_DIR/outputs" "$INSTALL_DIR/downloads" "$INSTALL_DIR/logs"

echo "[5/5] Membuat command 'loopforge'..."
cat > "$BIN" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$INSTALL_DIR"
exec python "$INSTALL_DIR/main.py" "\$@"
EOF
chmod +x "$BIN"

echo
echo "=============================================="
echo "       INSTALASI LOOPFORGE SELESAI"
echo "=============================================="
echo
echo "Coba:"
echo "  loopforge --version"
echo
echo "Untuk video lokal:"
echo "  loopforge local /path/video.mp4 --duration 1h"
echo
echo "Untuk YouTube:"
echo "  loopforge youtube 'URL_YOUTUBE' --duration 1h"
echo
echo "Output:"
echo "  $INSTALL_DIR/outputs/"
echo
echo "Jika ingin mengakses penyimpanan Android:"
echo "  termux-setup-storage"
echo

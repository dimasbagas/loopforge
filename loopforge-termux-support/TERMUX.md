# LoopForge di Termux

LoopForge versi Windows menggunakan PowerShell, `winget`, dan `loopforge.exe`.
File `install-termux.sh` menyediakan installer khusus Android/Termux.

## Instalasi

```bash
pkg update
pkg install -y curl
curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-termux.sh | bash
```

## Pemakaian

```bash
loopforge --version
loopforge local /sdcard/Movies/video.mp4 --duration 1h
loopforge youtube "https://youtu.be/xxxxx" --duration 8h
```

Jika penyimpanan Android belum terhubung:

```bash
termux-setup-storage
```

Output disimpan di:

```text
$PREFIX/opt/loopforge/outputs/
```

## Catatan Android

- FFmpeg dijalankan melalui paket FFmpeg Termux.
- Tidak menggunakan `winget`, PowerShell, `.exe`, atau shortcut Windows.
- Dependency `opencv-python` tidak dipasang di Termux. Fitur `--seamless` akan nonaktif/bernilai 0 jika OpenCV tidak tersedia.
- Rendering menggunakan CPU (`libx264`) pada perangkat Android kecuali FFmpeg/device menyediakan encoder lain yang sesuai.

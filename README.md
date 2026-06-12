# 🔁 LoopForge

> **CLI tool untuk loop video YouTube atau lokal ke durasi target (1h, 8h, 24h, dll)**

[![Release](https://img.shields.io/github/v/release/dimasbagas/loopforge?style=flat-square&color=blue)](https://github.com/dimasbagas/loopforge/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://github.com/dimasbagas/loopforge/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## ⚡ Install (Satu Perintah)

Buka **PowerShell** dan jalankan:

```powershell
irm https://raw.githubusercontent.com/dimasbagas/loopforge/master/install.ps1 | iex
```

> Script ini akan otomatis install **FFmpeg** (jika belum ada) dan **LoopForge CLI**, lalu mendaftarkan ke PATH.

---

## 🚀 Cara Pakai

Setelah install, buka terminal baru dan ketik:

```powershell
# Interactive wizard (direkomendasikan untuk pemula)
loopforge

# Download & loop video YouTube ke 1 jam
loopforge youtube https://youtu.be/xxxxx -d 1h

# Download & loop ke 8 jam, simpan ke folder tertentu
loopforge youtube https://youtu.be/xxxxx -d 8h -o "D:\Music"

# Loop video lokal ke 24 jam
loopforge local "video.mp4" -d 24h

# Lihat info video tanpa render
loopforge info "video.mp4"
```

### Format Durasi

| Format | Durasi |
|--------|--------|
| `30m` | 30 menit |
| `1h` | 1 jam |
| `8h` | 8 jam |
| `24h` | 24 jam |
| `3600` | 3600 detik |

---

## ✅ Persyaratan

- **Windows 10/11** (64-bit)
- **PowerShell 5.1+**
- **FFmpeg** — diinstall otomatis oleh installer
- **Internet** — untuk download video YouTube

---

## 📁 Lokasi File Output

Setelah render selesai, video tersimpan di:

```
C:\Users\<nama>\AppData\Local\Programs\LoopForge\outputs\
```

---

## 🛠️ Fitur

- ✅ Download & loop video YouTube otomatis
- ✅ Loop video lokal (MP4, MKV, AVI, dll)
- ✅ Deteksi GPU NVIDIA untuk render lebih cepat (NVENC)
- ✅ Fallback ke CPU jika GPU tidak tersedia
- ✅ Progress bar real-time
- ✅ Analisis seamless loop (opsional)
- ✅ Support codec AV1, H.264, VP9

---

## 🐛 Troubleshooting

**`loopforge` tidak dikenali setelah install:**
> Tutup terminal dan buka terminal baru (PATH perlu direload)

**FFmpeg tidak ditemukan:**
> Install manual dari [ffmpeg.org](https://ffmpeg.org/download.html) atau jalankan `winget install Gyan.FFmpeg`

**Video gagal render dengan GPU:**
> Coba tambahkan flag `--no-gpu` (fitur coming soon) atau update driver NVIDIA

---

## 📜 License

MIT © [dimasbagas](https://github.com/dimasbagas)

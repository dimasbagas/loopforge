# 🔁 LoopForge

> **CLI tool modern untuk meloop video YouTube atau lokal ke durasi target (1h, 8h, 24h, dll) dengan dukungan akselerasi GPU & FFmpeg.**

[![Release](https://img.shields.io/github/v/release/dimasbagas/loopforge?style=flat-square&color=blue)](https://github.com/dimasbagas/loopforge/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android%20%7C%20macOS-blue?style=flat-square)](https://github.com/dimasbagas/loopforge/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

---

## 🖥️ Sistem Operasi yang Didukung & Persyaratan

LoopForge dapat dijalankan di berbagai Sistem Operasi. Berikut adalah prasyarat yang perlu disiapkan sebelum melakukan instalasi:

| OS / Platform | Status | Aplikasi/Tools yang Perlu Disiapkan Terlebih Dahulu |
| :--- | :---: | :--- |
| **Windows 10/11** (64-bit) | ✅ **Resmi** | • **PowerShell 5.1+** (Sudah ada di Windows)<br>• **Internet** (Untuk download video & installer)<br>• *FFmpeg akan diinstall otomatis oleh installer* |
| **Android / HP** | ✅ **Resmi** | • **[Termux App](https://f-droid.org/en/packages/com.termux/)** *(Wajib download dari F-Droid, **BUKAN** Play Store)*<br>• Perintah `termux-setup-storage` untuk akses galeri/memori HP |
| **Linux** (Ubuntu, Debian, Arch, Fedora) | ✅ **Resmi** | • **Python 3.10+** (`python3`, `python3-pip`, `python3-venv`)<br>• **FFmpeg** (`sudo apt install ffmpeg` / `sudo pacman -S ffmpeg`)<br>• **Git** (`sudo apt install git`) |
| **macOS** (Intel & Apple Silicon) | ✅ **Kompatibel** | • **Python 3.10+** (`brew install python`)<br>• **FFmpeg** (`brew install ffmpeg`)<br>• **Git** (`brew install git`) |

---

## ⚡ Cara Install (Pilih Metode Sesuai Kebutuhan)

### 🚀 Metode 1: One-Liner Auto Installer (Paling Mudah)

Installer otomatis akan mengkonfigurasi sistem, mendownload dependensi, dan mendaftarkan perintah `loopforge` ke terminal Anda.

#### 🖥️ Windows (PowerShell)
Buka **PowerShell** lalu jalankan:
```powershell
irm https://raw.githubusercontent.com/dimasbagas/loopforge/master/install.ps1 | iex
```
> *Script otomatis menginstall **FFmpeg** via winget (jika belum ada), mendownload **LoopForge CLI**, dan menambahkannya ke PATH.*

#### 📱 Android (Termux)
Buka aplikasi **Termux** lalu jalankan:
```bash
pkg update && pkg install -y curl
curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-termux.sh | bash
```
> *Script otomatis menginstall **Python**, **FFmpeg**, **yt-dlp**, dan mendaftarkan perintah `loopforge` di Termux.*

#### 🐧 Linux (Ubuntu / Debian / Arch / Fedora)
Buka **Terminal** lalu jalankan:
```bash
curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-linux.sh | bash
```
> *Script otomatis membuat virtual environment di `~/.local/share/loopforge` dan memasang file eksekusi di `~/.local/bin/loopforge`.*

---

### 📦 Metode 2: Portable Executable (.exe) — Windows Tanpa Install

Jika Anda tidak ingin menginstall Python atau script:
1. Buka [GitHub Releases LoopForge](https://github.com/dimasbagas/loopforge/releases/latest).
2. Download file `loopforge.exe`.
3. Pindahkan file `loopforge.exe` ke folder pilihan Anda (misalnya `C:\Tools\`).
4. Pastikan **FFmpeg** sudah terinstall di komputer Anda (`winget install Gyan.FFmpeg`).
5. Buka Command Prompt / PowerShell di folder tersebut dan jalankan:
   ```cmd
   .\loopforge.exe --help
   ```

---

### 🛠️ Metode 3: Manual / From Source (Git Clone) — Semua OS / Developer

Cocok untuk pengembang yang ingin mengubah kode sumber atau menggunakan di macOS/Linux:

1. **Clone repository:**
   ```bash
   git clone https://github.com/dimasbagas/loopforge.git
   cd loopforge
   ```

2. **Buat Virtual Environment (opsional tapi disarankan):**
   ```bash
   python -m venv .venv
   
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   
   # Linux / macOS / Termux:
   source .venv/bin/activate
   ```

3. **Install paket & dependensi:**
   ```bash
   pip install --upgrade pip
   pip install -e .
   ```

4. **Uji coba perintah:**
   ```bash
   loopforge --help
   ```

---

## 🚀 Cara Pakai

Setelah proses instalasi selesai, buka terminal/PowerShell baru dan gunakan perintah berikut:

### 1. Interactive Wizard (Sangat Direkomendasikan untuk Pemula)
Cukup ketik `loopforge` dan ikuti petunjuk visual interaktif:
```bash
loopforge
```

### 2. Download & Loop Video YouTube
```bash
# Loop video YouTube ke 1 jam
loopforge youtube https://youtu.be/xxxxx -d 1h

# Loop ke 8 jam dan simpan di folder khusus
loopforge youtube https://youtu.be/xxxxx -d 8h -o "D:\Videos\Output"
```

### 3. Loop Video Lokal
```bash
# Loop video lokal ke 24 jam
loopforge local "C:\Videos\sample.mp4" -d 24h

# Di Android / Termux:
loopforge local /sdcard/Movies/video.mp4 -d 2h
```

### 4. Cek Informasi Video
```bash
loopforge info "C:\Videos\sample.mp4"
```

---

### ⏱️ Format Penulisan Durasi Target

| Format | Keterangan | Contoh |
| :---: | :--- | :--- |
| `30m` | 30 Menit | `loopforge local video.mp4 -d 30m` |
| `1h` | 1 Jam | `loopforge youtube "URL" -d 1h` |
| `8h` | 8 Jam | `loopforge youtube "URL" -d 8h` |
| `24h` | 24 Jam | `loopforge local video.mp4 -d 24h` |
| `3600` | 3600 Detik | `loopforge local video.mp4 -d 3600` |

---

## 📂 Lokasi Output Render Per Sistem Operasi

| OS / Platform | Lokasi Default Simpan File Output |
| :--- | :--- |
| **Windows** | `C:\Users\<Username>\AppData\Local\Programs\LoopForge\outputs\` *(Installer)* atau folder aktif |
| **Android / Termux** | `$PREFIX/opt/loopforge/outputs/` |
| **Linux / macOS** | `$HOME/.local/share/loopforge/outputs/` atau folder project |

---

## 🐛 Troubleshooting & Jawaban Pertanyaan Umum (FAQ)

<details>
<summary><b>1. Mengapa di Termux muncul error "No command irm found"?</b></summary>
<br>
Perintah <code>irm</code> dan <code>iex</code> adalah perintah khusus <b>Windows PowerShell</b>. Untuk Android (Termux), Anda wajib menggunakan command berikut:<br>
<code>curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/install-termux.sh | bash</code>
</details>

<details>
<summary><b>2. Mengapa LoopForge di Termux tidak bisa membaca file video dari memori HP?</b></summary>
<br>
Termux membutuhkan izin akses penyimpanan Android. Jalankan perintah ini di Termux:<br>
<code>termux-setup-storage</code><br>
Setelah itu, file galeri/internal Anda dapat diakses di lokasi <code>/sdcard/</code> atau <code>/storage/emulated/0/</code>.
</details>

<details>
<summary><b>3. Mengapa Termux F-Droid yang direkomendasikan, bukan Play Store?</b></summary>
<br>
Aplikasi Termux di Google Play Store sudah <b>tidak diupdate lagi (deprecated)</b> dan mengalami kendala instalasi paket <code>pkg</code>. Selalu download Termux terbaru dari <a href="https://f-droid.org/en/packages/com.termux/">F-Droid</a>.
</details>

<details>
<summary><b>4. Command `loopforge` tidak ditemukan setelah install?</b></summary>
<br>
Tutup terminal Anda dan buka terminal yang baru agar variable <code>PATH</code> diperbarui oleh sistem.
</details>

<details>
<summary><b>5. Apakah render mendukung Akselerasi GPU (NVIDIA NVENC)?</b></summary>
<br>
Ya! Di Windows/Linux dengan Kartu Grafis NVIDIA, LoopForge secara otomatis mendeteksi driver NVENC untuk mempercepat proses render video hingga 5x-10x lebih cepat dibanding CPU.
</details>

---

## 🗑️ Cara Uninstall (Semua OS)

#### 🖥️ Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/dimasbagas/loopforge/master/uninstall.ps1 | iex
```

#### 📱 Android (Termux):
```bash
curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/uninstall-termux.sh | bash
```

#### 🐧 Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/dimasbagas/loopforge/master/uninstall-linux.sh | bash
```

---

## 📜 Lisensi

Lisensi **MIT** © [dimasbagas](https://github.com/dimasbagas) — Bebas digunakan, dimodifikasi, dan didistribusikan.

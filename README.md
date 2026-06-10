# LoopForge CLI

**Ubah video pendek menjadi video berdurasi panjang dengan looping otomatis.**

Cocok untuk content creator, ambient channel, lofi creator, sleep music creator, dan microstock creator.

## Fitur

- **Loop Video Lokal** - Import video dan loop hingga durasi target
- **Download YouTube + Loop** - Download video YouTube, lalu loop otomatis
- **Info Video** - Tampilkan metadata video lengkap
- **Batch Processing** - Proses banyak video sekaligus
- **GPU NVIDIA NVENC** - Deteksi otomatis dan render dengan GPU
- **Fast Mode** - Copy stream tanpa re-encode untuk kecepatan maksimal
- **Seamless Loop Analysis** - Analisis transisi loop menggunakan OpenCV
- **Metadata Report** - Output JSON metadata setiap render
- **Terminal UI** - Progress bar, ETA, dan informasi real-time dengan Rich

## Instalasi

### 1. Install Python 3.12+

**Windows:** Download dari [python.org](https://www.python.org/downloads/) atau:
```bash
winget install Python.Python.3.12
```

**macOS:**
```bash
brew install python@3.12
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install python3.12 python3.12-venv
```

### 2. Install FFmpeg

**Windows:**
```bash
winget install FFmpeg
```
Atau download manual dari [ffmpeg.org](https://ffmpeg.org/download.html) dan tambahkan ke PATH.

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

### 3. Install yt-dlp

```bash
pip install yt-dlp
```

Atau download dari [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp).

### 4. Install uv (Package Manager)

```bash
pip install uv
```

### 5. Install LoopForge

```bash
# Clone atau copy project
cd loopforge

# Install dependencies
uv sync

# Atau dengan pip
pip install -e .
```

## Cara Penggunaan

### Loop Video Lokal

```bash
# Loop 1 jam (default)
loopforge local video.mp4

# Loop 8 jam
loopforge local video.mp4 --duration 8h

# Loop 12 jam
loopforge local video.mp4 -d 12h

# Fast mode (copy stream, tanpa re-encode)
loopforge local video.mp4 -d 2h --fast

# Analisis seamless loop
loopforge local video.mp4 -d 1h --seamless
```

### Download YouTube + Loop

```bash
# Download lalu loop 1 jam
loopforge youtube https://youtube.com/watch?v=xxxxx

# Download lalu loop 12 jam
loopforge youtube https://youtu.be/xxxxx -d 12h
```

### Info Video

```bash
loopforge info video.mp4
```

Output:
```
File Name: video.mp4
Resolution: 1920x1080
FPS: 30.00
Codec: h264
Duration: 00:01:00
Bitrate: 5000 kbps
File Size: 35.23 MB
```

### Batch Processing

```bash
# Loop semua video di folder
loopforge batch ./videos --duration 8h
```

## Format Durasi

| Format | Contoh | Hasil |
|--------|--------|-------|
| Jam | `1h`, `2h`, `8h`, `12h`, `24h` | 3600, 7200, 28800, 43200, 86400 detik |
| Menit | `90m`, `120m` | 5400, 7200 detik |
| Detik | `3600s` | 3600 detik |
| HH:MM:SS | `01:30:00`, `10:00:00` | 5400, 36000 detik |
| MM:SS | `90:00` | 5400 detik |

## Struktur Project

```
loopforge/
├── src/
│   ├── cli.py              # CLI entry point
│   ├── config.py            # Konfigurasi global
│   ├── commands/
│   │   ├── local.py         # Loop video lokal
│   │   ├── youtube.py       # Download YouTube + loop
│   │   ├── info.py          # Info video
│   │   ├── batch.py         # Batch processing
│   ├── services/
│   │   ├── ffmpeg_service.py   # FFmpeg/FFprobe wrapper
│   │   ├── youtube_service.py  # YouTube download
│   │   ├── duration_service.py # Parser durasi
│   │   ├── gpu_service.py      # GPU detection
│   │   ├── metadata_service.py # Metadata JSON
│   ├── utils/
│   │   ├── logger.py          # Logging
│   │   ├── validator.py       # Validasi input
│   ├── models/                 # Pydantic models
├── outputs/                  # Hasil render
├── downloads/                # Video hasil download
├── logs/                     # File log
├── tests/                    # Unit tests
├── pyproject.toml
└── README.md
```

## GPU Support

LoopForge secara otomatis mendeteksi GPU NVIDIA dan menggunakan encoder **h264_nvenc**.

Jika GPU NVIDIA tersedia:
```
GPU Detected: NVIDIA GeForce RTX 4060
Encoder: h264_nvenc
```

Jika tidak ada GPU:
```
GPU Not Found
Using: libx264
```

## Output

Semua hasil render disimpan di folder `outputs/` dengan penamaan otomatis:
- `video_1h.mp4`
- `video_8h.mp4`
- `video_12h.mp4`
- `video_24h.mp4`

Format output: **MP4 H.264** dengan audio AAC (192kbps).

## Metadata

Setiap render menghasilkan file JSON metadata:
```json
{
  "source_duration": "00:01:00",
  "target_duration": "10:00:00",
  "total_loops": 600,
  "encoder": "h264_nvenc",
  "resolution": "1920x1080",
  "output_file": "video_10h.mp4"
}
```

## Build Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --console --name loopforge src/cli.py

# Atau gunakan uv
uv run pyinstaller --onefile --console --name loopforge src/cli.py
```

Executable akan tersedia di `dist/loopforge.exe`.

## Unit Tests

```bash
# Install pytest
pip install pytest

# Jalankan tests
pytest tests/ -v
```

## Error Handling

LoopForge menangani berbagai skenario error:
- URL YouTube tidak valid
- Video tidak ditemukan
- FFmpeg/FFprobe belum terinstall
- yt-dlp belum terinstall
- Format durasi tidak valid
- File corrupt
- GPU encoder gagal
- Storage penuh

## System Requirements

- **OS:** Windows 10+, macOS 12+, Linux
- **Python:** 3.12+
- **Disk:** Tergantung durasi output (estimasi ditampilkan sebelum render)
- **RAM:** 512 MB minimal, 4 GB direkomendasikan
- **GPU:** NVIDIA dengan NVENC (opsional, untuk render lebih cepat)

## Lisensi

MIT

# LoopForge Online Installer
# Usage: irm https://raw.githubusercontent.com/dimasbagas/loopforge/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$GITHUB_REPO = "dimasbagas/loopforge"
$INSTALL_DIR = "$env:USERPROFILE\AppData\Local\Programs\LoopForge"

function Write-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "    _                    ___                    " -ForegroundColor Cyan
    Write-Host "   | |    ___   ___  _ _| __| ___  _ _ __ _ ___" -ForegroundColor Cyan
    Write-Host "   | |__ / _ \ / _ \| '_ \ _/ _ \| '_/ _' / -_)" -ForegroundColor Cyan
    Write-Host "   |____|\___/ \___/| .__/_|\___/|_| \__, \___|" -ForegroundColor Cyan
    Write-Host "                    |_|               |___/     " -ForegroundColor Cyan
    Write-Host ""
    Write-Host "          LoopForge CLI Installer v1.0.0         " -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "  [*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "    [+] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "    [!] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "    [-] $Message" -ForegroundColor Red
}

# ─────────────────────────────────────
# STEP 1: Check & Install FFmpeg
# ─────────────────────────────────────
function Install-FFmpeg {
    Write-Step "Memeriksa FFmpeg..."

    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        $version = (ffmpeg -version 2>&1 | Select-Object -First 1) -replace "ffmpeg version ", ""
        Write-Success "FFmpeg sudah terinstall: $version"
        return
    }

    Write-Warning "FFmpeg tidak ditemukan. Menginstall via winget..."

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Fail "winget tidak tersedia. Install FFmpeg secara manual dari https://ffmpeg.org/download.html"
        Write-Fail "Kemudian jalankan installer ini kembali."
        Read-Host "Tekan Enter untuk keluar..."
        exit 1
    }

    try {
        winget install --id Gyan.FFmpeg --source winget --accept-source-agreements --accept-package-agreements --silent
        Write-Success "FFmpeg berhasil diinstall!"
        Write-Warning "Restart terminal mungkin diperlukan agar FFmpeg terbaca di PATH."
    }
    catch {
        Write-Fail "Gagal install FFmpeg otomatis. Install manual dari https://ffmpeg.org"
        exit 1
    }
}

# ─────────────────────────────────────
# STEP 2: Download loopforge.exe dari GitHub Releases
# ─────────────────────────────────────
function Get-LatestRelease {
    Write-Step "Mengambil versi terbaru dari GitHub..."

    try {
        $api = "https://api.github.com/repos/$GITHUB_REPO/releases/latest"
        $headers = @{ "User-Agent" = "LoopForge-Installer" }
        $release = Invoke-RestMethod -Uri $api -Headers $headers

        $asset = $release.assets | Where-Object { $_.name -eq "loopforge.exe" } | Select-Object -First 1

        if (-not $asset) {
            Write-Fail "loopforge.exe tidak ditemukan di release terbaru!"
            exit 1
        }

        Write-Success "Versi terbaru: $($release.tag_name)"
        return $asset.browser_download_url
    }
    catch {
        Write-Fail "Gagal mengambil informasi release dari GitHub: $_"
        exit 1
    }
}

function Download-LoopForge {
    param([string]$Url)

    Write-Step "Mendownload loopforge.exe..."
    Write-Host "    URL: $Url" -ForegroundColor Gray

    $TempFile = "$env:TEMP\loopforge_download.exe"

    try {
        Invoke-WebRequest -Uri $Url -OutFile $TempFile -UseBasicParsing
        Write-Success "Download selesai!"
        return $TempFile
    }
    catch {
        Write-Fail "Gagal download: $_"
        exit 1
    }
}

# ─────────────────────────────────────
# STEP 3: Install
# ─────────────────────────────────────
function Install-LoopForge {
    param([string]$SourceFile)

    Write-Step "Menginstall LoopForge ke sistem..."
    Write-Host "    Lokasi: $INSTALL_DIR" -ForegroundColor Gray

    # Buat folder instalasi
    if (Test-Path $INSTALL_DIR) {
        Remove-Item $INSTALL_DIR -Recurse -Force -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

    # Copy exe
    Copy-Item -Path $SourceFile -Destination "$INSTALL_DIR\loopforge.exe" -Force
    Write-Success "File berhasil dikopi"

    # Buat folder kerja
    New-Item -ItemType Directory -Path "$INSTALL_DIR\outputs" -Force | Out-Null
    New-Item -ItemType Directory -Path "$INSTALL_DIR\downloads" -Force | Out-Null
    New-Item -ItemType Directory -Path "$INSTALL_DIR\logs" -Force | Out-Null
    Write-Success "Folder outputs, downloads, logs dibuat"
}

# ─────────────────────────────────────
# STEP 4: Setup PATH
# ─────────────────────────────────────
function Setup-Path {
    Write-Step "Mendaftarkan ke Environment PATH..."

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -notlike "*LoopForge*") {
        $NewPath = "$UserPath;$INSTALL_DIR"
        [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
        Write-Success "Berhasil terdaftar di PATH!"
    } else {
        Write-Success "Sudah terdaftar di PATH"
    }
}

# ─────────────────────────────────────
# STEP 5: Desktop Shortcut
# ─────────────────────────────────────
function Create-Shortcut {
    Write-Step "Membuat shortcut di Desktop..."

    try {
        $WshShell = New-Object -ComObject WScript.Shell
        $ShortcutPath = "$env:USERPROFILE\Desktop\LoopForge.lnk"
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-NoExit -Command `"loopforge`""
        $Shortcut.WorkingDirectory = "$env:USERPROFILE"
        $Shortcut.IconLocation = "$INSTALL_DIR\loopforge.exe,0"
        $Shortcut.Description = "LoopForge - Video Looper CLI"
        $Shortcut.Save()
        Write-Success "Shortcut Desktop dibuat!"
    }
    catch {
        Write-Warning "Tidak bisa membuat shortcut: $_"
    }
}

# ─────────────────────────────────────
# MAIN
# ─────────────────────────────────────
Write-Banner

Install-FFmpeg
$DownloadUrl = Get-LatestRelease
$TempExe = Download-LoopForge -Url $DownloadUrl
Install-LoopForge -SourceFile $TempExe
Setup-Path
Create-Shortcut

# Cleanup
Remove-Item $TempExe -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "            [+] INSTALASI SELESAI!                         " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Cara memulai:" -ForegroundColor Cyan
Write-Host "    1. TUTUP terminal ini dan buka terminal BARU" -ForegroundColor White
Write-Host "    2. Ketik: loopforge" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Atau klik shortcut 'LoopForge' di Desktop!" -ForegroundColor White
Write-Host ""
Read-Host "Tekan Enter untuk keluar..."

# ============================================================
#  LoopForge Installer (Windows 10/11 64-bit)
#
#  Satu perintah -> LoopForge + FFmpeg terpasang otomatis.
#  Tidak butuh Python, winget, Microsoft Store, atau admin.
#
#  Pakai:
#    irm https://raw.githubusercontent.com/dimasbagas/loopforge/master/install.ps1 | iex
#
#  Opsi environment (untuk CI / instalasi khusus):
#    LOOPFORGE_INSTALL_DIR   -> folder instalasi lain
#    LOOPFORGE_SKIP_PATH=1   -> jangan ubah PATH
#    LOOPFORGE_SKIP_SHORTCUT=1 -> jangan buat shortcut Desktop
# ============================================================

$LF_PREV_EAP = $ErrorActionPreference
$LF_PREV_PP  = $ProgressPreference

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

$LF_REPO        = "dimasbagas/loopforge"
$LF_EXE_URL     = "https://github.com/$LF_REPO/releases/latest/download/loopforge.exe"
$LF_INSTALL_DIR = if ($env:LOOPFORGE_INSTALL_DIR) { $env:LOOPFORGE_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "Programs\LoopForge" }
$LF_SKIP_PATH   = ($env:LOOPFORGE_SKIP_PATH -eq "1")

# Mirror FFmpeg portable. Dicoba berurutan sampai berhasil.
$LF_FFMPEG_MIRRORS = @(
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
    "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
)

function LF-WriteBanner {
    Write-Host ""
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |            LoopForge CLI Installer               |" -ForegroundColor Cyan
    Write-Host "  |        Video looper + FFmpeg, sekali jalan       |" -ForegroundColor Cyan
    Write-Host "  +--------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
}

function LF-WriteStep {
    param([string]$Message)
    Write-Host "  [*] $Message" -ForegroundColor Cyan
}

function LF-WriteSuccess {
    param([string]$Message)
    Write-Host "    [+] $Message" -ForegroundColor Green
}

function LF-WriteWarning {
    param([string]$Message)
    Write-Host "    [!] $Message" -ForegroundColor Yellow
}

function LF-WriteFail {
    param([string]$Message)
    Write-Host "    [-] $Message" -ForegroundColor Red
}

function LF-Download {
    param(
        [string]$Url,
        [string]$OutFile
    )

    for ($attempt = 1; $attempt -le 2; $attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
            return
        } catch {
            if ($attempt -eq 2) { throw }
            Start-Sleep -Seconds 2
        }
    }
}

function LF-HasFfmpeg {
    foreach ($name in @("ffmpeg", "ffprobe")) {
        $cmd = Get-Command "$name.exe" -ErrorAction SilentlyContinue
        if (-not $cmd) { return $false }
        try {
            & $cmd.Source -version *> $null
        } catch {
            return $false
        }
    }
    return $true
}

function LF-InstallLoopForge {
    LF-WriteStep "Mendownload LoopForge terbaru..."

    $tmp = Join-Path $env:TEMP "loopforge_$PID.exe"

    try {
        LF-Download -Url $LF_EXE_URL -OutFile $tmp
    } catch {
        LF-WriteWarning "Download langsung gagal, mencoba lewat GitHub API..."
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$LF_REPO/releases/latest" -Headers @{ "User-Agent" = "LoopForge-Installer" }
        $asset = $release.assets | Where-Object { $_.name -eq "loopforge.exe" } | Select-Object -First 1
        if (-not $asset) { throw "Release terbaru tidak menyediakan loopforge.exe." }
        LF-Download -Url $asset.browser_download_url -OutFile $tmp
    }

    $size = (Get-Item $tmp).Length
    if ($size -lt 5MB) {
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        throw "File download tidak valid ($([math]::Round($size / 1MB, 1)) MB). Coba lagi beberapa saat."
    }

    try {
        Copy-Item -Path $tmp -Destination (Join-Path $LF_INSTALL_DIR "loopforge.exe") -Force
    } catch {
        throw "Gagal menyalin loopforge.exe. Tutup LoopForge yang sedang berjalan, lalu jalankan installer ini lagi."
    } finally {
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    }

    LF-WriteSuccess "LoopForge terpasang ($([math]::Round($size / 1MB, 1)) MB)."
}

function LF-InstallFfmpeg {
    $zip = Join-Path $env:TEMP "loopforge_ffmpeg_$PID.zip"

    foreach ($url in $LF_FFMPEG_MIRRORS) {
        try {
            LF-WriteStep "Mendownload FFmpeg (sekitar 80-130 MB, sekali saja)..."
            Write-Host "    $url" -ForegroundColor DarkGray
            LF-Download -Url $url -OutFile $zip

            LF-WriteStep "Mengekstrak ffmpeg.exe dan ffprobe.exe..."
            Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
            Add-Type -AssemblyName System.IO.Compression -ErrorAction SilentlyContinue

            $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
            try {
                foreach ($exe in @("ffmpeg.exe", "ffprobe.exe")) {
                    $entry = $archive.Entries |
                        Where-Object { $_.Name -eq $exe -and $_.FullName -like "*bin*" } |
                        Select-Object -First 1

                    if (-not $entry) { throw "$exe tidak ditemukan di dalam arsip." }

                    $dest       = Join-Path $LF_INSTALL_DIR $exe
                    $entryStream = $entry.Open()
                    $fileStream  = [System.IO.File]::Create($dest)
                    try {
                        $entryStream.CopyTo($fileStream)
                    } finally {
                        $fileStream.Dispose()
                        $entryStream.Dispose()
                    }
                }
            } finally {
                $archive.Dispose()
            }

            Remove-Item $zip -Force -ErrorAction SilentlyContinue
            LF-WriteSuccess "FFmpeg siap dipakai (portable, tanpa install global)."
            return $true
        } catch {
            LF-WriteWarning "Mirror gagal: $($_.Exception.Message)"
            Remove-Item $zip -Force -ErrorAction SilentlyContinue
        }
    }

    return $false
}

function LF-AddToUserPath {
    param([string]$Dir)

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $entries  = @($userPath -split ";" | ForEach-Object { $_.Trim() } | Where-Object { $_ })

    $already = $entries | Where-Object { $_.TrimEnd("\") -ieq $Dir.TrimEnd("\") }
    if (-not $already) {
        $newPath = (@($entries) + $Dir) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        LF-WriteSuccess "Folder instalasi ditambahkan ke PATH (permanen)."
    } else {
        LF-WriteSuccess "Folder instalasi sudah ada di PATH."
    }

    $inSession = ($env:Path -split ";") | Where-Object { $_.TrimEnd("\") -ieq $Dir.TrimEnd("\") }
    if (-not $inSession) {
        $env:Path = "$env:Path;$Dir"
    }
}

function LF-CreateShortcut {
    try {
        $shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "LoopForge.lnk"
        $shell    = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath       = Join-Path $LF_INSTALL_DIR "loopforge.exe"
        $shortcut.WorkingDirectory = $LF_INSTALL_DIR
        $shortcut.IconLocation     = "$LF_INSTALL_DIR\loopforge.exe,0"
        $shortcut.Description      = "LoopForge - Video Looper CLI"
        $shortcut.Save()
        LF-WriteSuccess "Shortcut Desktop dibuat."
    } catch {
        LF-WriteWarning "Shortcut Desktop tidak bisa dibuat: $($_.Exception.Message)"
    }
}

function LF-Verify {
    $exe = Join-Path $LF_INSTALL_DIR "loopforge.exe"
    $ff  = Join-Path $LF_INSTALL_DIR "ffmpeg.exe"

    LF-WriteStep "Memverifikasi hasil instalasi..."

    try {
        & $exe --help *> $null
        if ($LASTEXITCODE -eq 0) {
            LF-WriteSuccess "loopforge.exe berjalan normal."
        } else {
            LF-WriteWarning "loopforge.exe mengembalikan kode $LASTEXITCODE saat diuji."
        }
    } catch {
        LF-WriteWarning "loopforge.exe belum bisa dijalankan otomatis."
    }

    if (Test-Path $ff) {
        try {
            & $ff -version *> $null
            if ($LASTEXITCODE -eq 0) {
                LF-WriteSuccess "FFmpeg berjalan normal."
            } else {
                LF-WriteWarning "FFmpeg mengembalikan kode $LASTEXITCODE saat diuji."
            }
        } catch {
            LF-WriteWarning "FFmpeg belum bisa dijalankan otomatis."
        }
    }
}

function LF-Main {
    LF-WriteBanner

    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "LoopForge hanya tersedia untuk Windows 64-bit."
    }

    Write-Host "  Lokasi instalasi: $LF_INSTALL_DIR" -ForegroundColor DarkGray
    Write-Host ""

    New-Item -ItemType Directory -Path $LF_INSTALL_DIR -Force | Out-Null
    foreach ($sub in @("outputs", "downloads", "logs")) {
        New-Item -ItemType Directory -Path (Join-Path $LF_INSTALL_DIR $sub) -Force | Out-Null
    }

    LF-InstallLoopForge

    $ffmpegReady = $false
    $bundledFfmpeg = (Test-Path (Join-Path $LF_INSTALL_DIR "ffmpeg.exe")) -and
                     (Test-Path (Join-Path $LF_INSTALL_DIR "ffprobe.exe"))

    if ($bundledFfmpeg) {
        LF-WriteSuccess "FFmpeg portable sudah ada di folder instalasi."
        $ffmpegReady = $true
    } elseif (LF-HasFfmpeg) {
        LF-WriteSuccess "FFmpeg sudah tersedia di PATH, tidak perlu download ulang."
        $ffmpegReady = $true
    } else {
        LF-WriteWarning "FFmpeg belum terdeteksi. Memasang versi portable..."
        $ffmpegReady = LF-InstallFfmpeg
        if (-not $ffmpegReady) {
            LF-WriteWarning "FFmpeg gagal dipasang otomatis. Install manual dari https://ffmpeg.org lalu jalankan ulang installer."
        }
    }

    if ($LF_SKIP_PATH) {
        LF-WriteWarning "LOOPFORGE_SKIP_PATH=1 -> PATH tidak diubah."
    } else {
        LF-AddToUserPath -Dir $LF_INSTALL_DIR
    }

    if ($env:LOOPFORGE_SKIP_SHORTCUT -eq "1") {
        LF-WriteWarning "LOOPFORGE_SKIP_SHORTCUT=1 -> shortcut tidak dibuat."
    } else {
        LF-CreateShortcut
    }

    LF-Verify

    Write-Host ""
    Write-Host "  ====================================================" -ForegroundColor Green
    if ($ffmpegReady) {
        Write-Host "        [+] INSTALASI SELESAI - SEMUA SIAP PAKAI" -ForegroundColor Green
    } else {
        Write-Host "        [!] LOOPFORGE TERPASANG, FFMPEG BELUM" -ForegroundColor Yellow
    }
    Write-Host "  ====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Langkah berikutnya:" -ForegroundColor Cyan
    Write-Host "    1. Tutup PowerShell ini, buka terminal BARU." -ForegroundColor White
    Write-Host "    2. Ketik: " -ForegroundColor White -NoNewline
    Write-Host "loopforge" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Output video ada di: $LF_INSTALL_DIR\outputs" -ForegroundColor DarkGray
}

try {
    LF-Main
} catch {
    Write-Host ""
    LF-WriteFail $_.Exception.Message
    Write-Host ""
    Write-Host "  Install manual: https://github.com/dimasbagas/loopforge#-cara-install" -ForegroundColor Yellow
} finally {
    $ErrorActionPreference = $LF_PREV_EAP
    $ProgressPreference    = $LF_PREV_PP
}

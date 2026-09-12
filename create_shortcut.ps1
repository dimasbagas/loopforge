# LoopForge Desktop Shortcut Creator
# Jalankan script ini untuk membuat shortcut LoopForge di Desktop

$ErrorActionPreference = "Stop"

Write-Host "Membuat LoopForge Desktop Shortcut..." -ForegroundColor Cyan

# Cari loopforge.exe di PATH
$LoopForgeExe = (Get-Command loopforge -ErrorAction SilentlyContinue).Source

if (-not $LoopForgeExe) {
    Write-Host "ERROR: loopforge.exe tidak ditemukan di PATH!" -ForegroundColor Red
    Write-Host "Pastikan LoopForge sudah terinstall dan terdaftar di PATH." -ForegroundColor Yellow
    Read-Host "Tekan Enter untuk keluar"
    exit 1
}

Write-Host "  Lokasi loopforge.exe: $LoopForgeExe" -ForegroundColor Gray

# Buat shortcut
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $ShortcutPath = Join-Path $env:USERPROFILE "Desktop\LoopForge.lnk"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = '-NoExit -Command "loopforge"'
    $Shortcut.WorkingDirectory = $env:USERPROFILE
    $Shortcut.IconLocation = "$LoopForgeExe,0"
    $Shortcut.Description = "LoopForge - Video Looper CLI"
    $Shortcut.Save()
    
    Write-Host ""
    Write-Host "Shortcut berhasil dibuat di Desktop!" -ForegroundColor Green
    Write-Host "  Lokasi: $ShortcutPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Double-click icon 'LoopForge' di Desktop untuk memulai!" -ForegroundColor Cyan
}
catch {
    Write-Host "ERROR: Gagal membuat shortcut - $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Read-Host "Tekan Enter untuk keluar"

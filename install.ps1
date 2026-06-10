# LoopForge Offline Production Installer
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "            LoopForge -- AI Terminal Video Looper            " -ForegroundColor Cyan
Write-Host "                    Installer Script                        " -ForegroundColor Cyan
Write-Host "                   Production Release v1.0.0                " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$InstallDir = "$env:USERPROFILE\AppData\Local\Programs\LoopForge"

# 1. Locate local source directory/file
$SourceFile = "$PSScriptRoot\dist\loopforge.exe"
if (-not (Test-Path $SourceFile)) {
    $SourceFile = "$PSScriptRoot\loopforge.exe"
}

if (-not (Test-Path $SourceFile)) {
    Write-Host "  [-] Error: loopforge.exe not found!" -ForegroundColor Red
    Write-Host "  [-] Expected location: $SourceFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Make sure you have compiled the application or extracted the complete package." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit..."
    Exit 1
}

# 2. Prepare installation directory
Write-Host "  [*] Creating installation directory..." -ForegroundColor Cyan
Write-Host "    Location: $InstallDir" -ForegroundColor Gray
if (Test-Path $InstallDir) {
    Write-Host "    Removing existing installation..." -ForegroundColor Gray
    Remove-Item $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Write-Host "    [+] Directory ready" -ForegroundColor Green

# 3. Copy executable (100% Offline)
Write-Host "  [*] Copying application files..." -ForegroundColor Cyan
Write-Host "    This may take a moment..." -ForegroundColor Gray
Copy-Item -Path $SourceFile -Destination "$InstallDir\loopforge.exe" -Force
Write-Host "    [+] Files copied successfully" -ForegroundColor Green

# 4. Create program working directories
Write-Host "  [*] Creating working directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path "$InstallDir\outputs" -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallDir\downloads" -Force | Out-Null
New-Item -ItemType Directory -Path "$InstallDir\logs" -Force | Out-Null
Write-Host "    [+] Working directories ready" -ForegroundColor Green

# 5. Add to User Environment PATH
Write-Host "  [*] Registering in Environment PATH..." -ForegroundColor Cyan
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*LoopForge*") {
    $NewPath = "$UserPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "    [+] Registered globally in Environment PATH!" -ForegroundColor Green
    Write-Host "    [!] Please RESTART your PowerShell terminal to load 'loopforge' command." -ForegroundColor Yellow
} else {
    Write-Host "    [+] Already registered in PATH" -ForegroundColor Green
}

# 6. Create Desktop Shortcut
Write-Host "  [*] Creating Desktop Shortcut..." -ForegroundColor Cyan
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $ShortcutPath = "$env:USERPROFILE\Desktop\LoopForge.lnk"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "$InstallDir\loopforge.exe"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.IconLocation = "$InstallDir\loopforge.exe,0"
    $Shortcut.Save()
    Write-Host "    [+] Desktop shortcut created" -ForegroundColor Green
} catch {
    Write-Host "    [!] Could not create shortcut: $_" -ForegroundColor Yellow
}

# 7. Verification
Write-Host "  [*] Verifying installation..." -ForegroundColor Cyan
if (Test-Path "$InstallDir\loopforge.exe") {
    Write-Host "    [+] Installation verified successfully!" -ForegroundColor Green
} else {
    Write-Host "    [-] Installation verification failed" -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "              [+] INSTALLATION COMPLETED!                   " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Program Location:" -ForegroundColor Cyan
Write-Host "     $InstallDir" -ForegroundColor Gray
Write-Host ""
Write-Host "  How to Launch:" -ForegroundColor Cyan
Write-Host "     1. Close this window and open a NEW PowerShell or Command Prompt" -ForegroundColor Gray
Write-Host "     2. Type: loopforge --help" -ForegroundColor Gray
Write-Host "     3. Or double-click the LoopForge icon on your Desktop!" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit..."

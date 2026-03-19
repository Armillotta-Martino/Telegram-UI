# PowerShell helper to build a single-file Windows executable with PyInstaller
# Usage: Open the venv and run: .\scripts\build_windows_exe.ps1

# Ensure virtualenv is active and PyInstaller is installed
pyinstaller --noconfirm --clean --onefile --windowed `
  --name "Telegram-UI" `
  --add-data "ffmpeg;ffmpeg" `
  --add-data "images;images" `
  --add-data "icons;icons" `
  --icon docs/images/logo.ico `
  src/main.py

Write-Host "Build finished. Check the dist\Telegram-UI folder for the executable."
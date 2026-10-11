@echo off
REM Simple Windows batch script to build the executable
REM Usage: build.bat [clean|windows|include-ini]

echo 🚀 Zoom Poll Analyzer Build Script
echo.

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%

cd /d "%PROJECT_DIR%"

if "%1"=="clean" (
    echo 🧹 Cleaning build artifacts...
    python scripts\build_executable.py --clean
    goto :end
)

if "%1"=="include-ini" (
    echo 📦 Building executable with INI file...
    python scripts\build_executable.py --include-ini
    goto :end
)

echo 📦 Building executable for Windows...
python scripts\build_executable.py --platform windows

:end
echo.
echo ✅ Build script completed!
pause

@echo off
setlocal
echo Packaging MasterSK Blender Addon...
python "%~dp0build_addon.py"
if %ERRORLEVEL% equ 0 (
    echo.
    echo ==========================================================
    echo  SUCCESS! MasterSK.zip is ready for Blender installation.
    echo ==========================================================
) else (
    echo.
    echo Build failed. Please ensure Python is installed and in PATH.
)
echo.
if "%~1" neq "--no-pause" pause

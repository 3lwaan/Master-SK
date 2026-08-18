@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Master SK Blender Addon Builder
echo ===================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "ZIP_NAME=master_sk_tools.zip"
set "BUILD_DIR=%SCRIPT_DIR%build"
set "PACKAGE_DIR=%BUILD_DIR%\MasterSK"
set "OUTPUT_ZIP=%SCRIPT_DIR%%ZIP_NAME%"

echo [*] Cleaning previous build artifacts...
if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"
if exist "%OUTPUT_ZIP%" del /q "%OUTPUT_ZIP%"

echo [*] Creating build directory structure...
mkdir "%PACKAGE_DIR%"

echo [*] Copying addon source files...
copy "%SCRIPT_DIR%__init__.py" "%PACKAGE_DIR%\" >nul
copy "%SCRIPT_DIR%ui_panel.py" "%PACKAGE_DIR%\" >nul
copy "%SCRIPT_DIR%operators.py" "%PACKAGE_DIR%\" >nul
copy "%SCRIPT_DIR%reference_loader.py" "%PACKAGE_DIR%\" >nul
copy "%SCRIPT_DIR%daz_g9_reference.py" "%PACKAGE_DIR%\" >nul
if exist "%SCRIPT_DIR%daz_g9_reference.json" copy "%SCRIPT_DIR%daz_g9_reference.json" "%PACKAGE_DIR%\" >nul
if exist "%SCRIPT_DIR%g9_nails_uv_reference.json" copy "%SCRIPT_DIR%g9_nails_uv_reference.json" "%PACKAGE_DIR%\" >nul
copy "%SCRIPT_DIR%rig_utils.py" "%PACKAGE_DIR%\" >nul
if exist "%SCRIPT_DIR%README.md" copy "%SCRIPT_DIR%README.md" "%PACKAGE_DIR%\" >nul
if exist "%SCRIPT_DIR%CHANGELOG.md" copy "%SCRIPT_DIR%CHANGELOG.md" "%PACKAGE_DIR%\" >nul
if exist "%SCRIPT_DIR%LICENSE" copy "%SCRIPT_DIR%LICENSE" "%PACKAGE_DIR%\" >nul

echo [*] Packaging addon into %ZIP_NAME%...
powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '%OUTPUT_ZIP%' -Force"

if exist "%OUTPUT_ZIP%" (
    echo.
    echo ===================================================
    echo  SUCCESS! Built: %OUTPUT_ZIP%
    echo ===================================================
    echo  You can now install master_sk_tools.zip directly
    echo  into Blender via Edit ^> Preferences ^> Add-ons.
    echo ===================================================
) else (
    echo.
    echo [!] ERROR: Failed to create zip package.
)

if exist "%BUILD_DIR%" rd /s /q "%BUILD_DIR%"

echo.
pause

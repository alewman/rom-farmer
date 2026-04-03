@echo off
REM Install Wii DLC WADs to Dolphin NAND (RetroBat)
REM
REM This script installs WAD files from the nand\ subfolder into the
REM Dolphin emulator's NAND storage, making DLC available in-game.
REM
REM Usage: Run from the wii-extras output directory
REM   cd %RETROBAT_DIR%\roms\wii\wii-extras
REM   install.bat

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "WAD_DIR=%SCRIPT_DIR%nand"

REM Auto-detect RetroBat Dolphin NAND path
if defined RETROBAT_DIR (
    set "NAND_DIR=%RETROBAT_DIR%\emulators\dolphin-emu\User\Wii"
) else (
    REM Fallback: look relative to script location
    for %%i in ("%SCRIPT_DIR%..\..\..") do set "RETROBAT_ROOT=%%~fi"
    set "NAND_DIR=!RETROBAT_ROOT!\emulators\dolphin-emu\User\Wii"
)

if not exist "%WAD_DIR%" (
    echo ERROR: nand\ directory not found at %WAD_DIR%
    exit /b 1
)

REM Count WADs
set WAD_COUNT=0
for %%f in ("%WAD_DIR%\*.wad") do set /a WAD_COUNT+=1

if %WAD_COUNT% equ 0 (
    echo No WAD files found in %WAD_DIR%
    exit /b 0
)

echo Installing %WAD_COUNT% WAD files to Dolphin NAND...
echo NAND directory: %NAND_DIR%
echo.

set INSTALLED=0
set FAILED=0

for %%f in ("%WAD_DIR%\*.wad") do (
    echo   Installing: %%~nxf ...

    REM Try dolphin-tool first
    where dolphin-tool >nul 2>&1
    if !errorlevel! equ 0 (
        dolphin-tool install --nand="%NAND_DIR%" "%%f" >nul 2>&1
        if !errorlevel! equ 0 (
            echo     OK
            set /a INSTALLED+=1
        ) else (
            goto :fallback_copy
        )
    ) else (
        :fallback_copy
        if not exist "%NAND_DIR%" mkdir "%NAND_DIR%"
        copy "%%f" "%NAND_DIR%\%%~nxf" >nul 2>&1
        if !errorlevel! equ 0 (
            echo     OK (copied^)
            set /a INSTALLED+=1
        ) else (
            echo     FAILED
            set /a FAILED+=1
        )
    )
)

echo.
echo Done: %INSTALLED% installed, %FAILED% failed (out of %WAD_COUNT%)

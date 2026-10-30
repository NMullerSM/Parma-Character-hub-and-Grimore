@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Compilador de Instalador Windows — Parma

echo ===================================================
echo  Parma — Compilador Inno Setup para Windows
echo ===================================================

set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not exist "%ISCC_PATH%" (
    echo [Error] No se encontro Inno Setup Compiler (ISCC.exe).
    echo Asegurate de instalar Inno Setup 6 desde: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

if not exist "..\Parma\Parma.exe" (
    echo [Aviso] No se detecto el build en ejecutables\windows\Parma.
    echo Compilando la aplicacion primero con build_desktop.py...
    pushd "..\..\..\"
    call python build_desktop.py
    popd
)

echo [Parma] Compilando instalador Setup...
"%ISCC_PATH%" "parma_setup.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================================
    echo  [Exito] Instalador generado en ejecutables\windows\
    echo ===================================================
) else (
    echo [Error] Fallo la compilacion con Inno Setup.
)

pause

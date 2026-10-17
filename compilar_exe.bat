@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Compilar DnD Sanctum a .EXE

echo ===================================================
echo  Compilador PyInstaller DnD Sanctum a .EXE
echo ===================================================

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [Error] No se encontro el entorno virtual en: "%~dp0.venv"
    pause
    exit /b 1
)

"%~dp0.venv\Scripts\python.exe" build_desktop.py %*
pause

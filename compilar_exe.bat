@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Compilar D&D Sanctum a .EXE

echo ===================================================
echo  Compilador PyInstaller D&D Sanctum a .EXE
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
    echo [Error] No se encontró el entorno virtual .venv en: %~dp0.venv
    pause
    exit /b 1
)

".venv\Scripts\python.exe" build_desktop.py %*
pause

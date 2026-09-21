@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Compilar Visualizador D^&D 5e a .EXE

echo ===================================================
echo  Compilador PyInstaller a Ejecutable .EXE
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
    echo [Error] No se encontro el entorno virtual .venv en: %~dp0.venv
    pause
    exit /b 1
)

".venv\Scripts\python.exe" flet_app\build_exe.py
pause

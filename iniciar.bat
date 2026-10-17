@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title DnD Sanctum - Character Hub and Grimoire

echo ===================================================
echo  DnD Sanctum - Lanzador de Escritorio (PyWebView)
echo ===================================================

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [Error] No se encontro el entorno virtual en: "%~dp0.venv"
    echo Por favor asegurate de inicializar el entorno virtual.
    pause
    exit /b 1
)

"%~dp0.venv\Scripts\python.exe" desktop_app.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Aviso] La aplicacion finalizo con codigo de salida %ERRORLEVEL%.
    pause
)

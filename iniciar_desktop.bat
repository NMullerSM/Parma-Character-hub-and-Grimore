@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Visualizador D^&D 5e - Desktop (Flet)

echo ===================================================
echo  Visualizador ^& Editor D^&D 5e - Flet Desktop Edition
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
    echo [Error] No se encontro el entorno virtual .venv en: %~dp0.venv
    echo Por favor asegurate de tener la carpeta .venv en el repositorio.
    pause
    exit /b 1
)

echo Iniciando aplicacion de escritorio...
".venv\Scripts\python.exe" -m flet_app.main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Aviso] La aplicacion finalizo con codigo de salida %ERRORLEVEL%.
    pause
)

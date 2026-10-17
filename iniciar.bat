@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title D&D Sanctum — Character Hub ^& Grimoire

echo ===================================================
echo  D^&D Sanctum — Lanzador de Escritorio (PyWebView)
echo ===================================================

if not exist ".venv\Scripts\python.exe" (
    echo [Error] No se encontró el entorno virtual en: %~dp0.venv
    echo Por favor asegúrate de inicializar el entorno virtual.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" desktop_app.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Aviso] La aplicación finalizó con código de salida %ERRORLEVEL%.
    pause
)

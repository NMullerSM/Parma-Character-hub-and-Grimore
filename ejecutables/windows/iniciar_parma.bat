@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ===================================================
echo  Parma — Lanzando Ejecutable Compilado (.EXE)
echo ===================================================

if not exist "%~dp0Parma\Parma.exe" (
    echo [Error] No se encontró el binario compilado en: "%~dp0Parma\Parma.exe"
    echo Ejecuta 'compilar_exe.bat' en la raíz para generar el ejecutable.
    pause
    exit /b 1
)

start "" "%~dp0Parma\Parma.exe" %*

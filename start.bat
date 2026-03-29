@echo off
title Erasmus LA Helper
echo ============================================================
echo   Erasmus LA Helper - Avvio
echo ============================================================
echo.

REM Controlla se Python e' installato
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato. Installalo da https://python.org
    pause
    exit /b 1
)

REM Installa dipendenze se necessario
echo Controllo dipendenze...
pip install -r requirements.txt --quiet

echo.
echo Avvio del server...
echo Apri il browser su: http://localhost:5050
echo.
echo Per fermare il server premi CTRL+C
echo ============================================================

python app.py

pause

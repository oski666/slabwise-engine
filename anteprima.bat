@echo off
rem Anteprima del sito Slabwise su Windows: ricostruisce la pagina e la apre nel browser.
rem Doppio clic su questo file, oppure da terminale: anteprima.bat
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py) || (set PY=python)
%PY% prototype\v7\build.py
if errorlevel 1 (
  echo.
  echo Qualcosa non va: leggi il messaggio qui sopra.
  pause
  exit /b 1
)
start "" "prototype\v7\slabwise.html"

@echo off
REM Ejecuta todo el observatorio en local: recolecta, valida, publica y avisa.
cd /d "%~dp0"
python -m observatorio run %*

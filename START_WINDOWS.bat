@echo off
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 goto usepython
py -3 server.py
goto end
:usepython
python server.py
:end
pause

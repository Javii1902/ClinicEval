@echo off
setlocal

rem %~dp0 is the folder this .bat file lives in, so this always runs the
rem tests for the copy of ClinicEval sitting alongside it, wherever that
rem folder is - no hardcoded path, so moving/copying the whole project
rem elsewhere still works without editing this file.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m pytest tests\
) else (
    echo No .venv found - falling back to system python. If pytest isn't
    echo installed there, run: pip install -r requirements-dev.txt
    echo.
    python -m pytest tests\
)

echo.
echo Press any key to close this window . . .
pause >nul

endlocal

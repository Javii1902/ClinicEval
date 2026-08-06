@echo off
setlocal enabledelayedexpansion

rem %~dp0 is the folder this .bat file lives in, so this always runs the
rem copy of ClinicEval sitting alongside it, wherever that folder is - no
rem hardcoded path, so moving/copying the whole project elsewhere still
rem works without editing this file.
cd /d "%~dp0"

rem A .venv folder bakes in an absolute path to the Python install it was
rem created against (see .venv\pyvenv.cfg). Copy the project to a different
rem computer - or even just reinstall/move Python on this one - and that
rem path stops existing, so .venv\Scripts\python.exe silently fails even
rem though the folder is right there. Detect that instead of assuming a
rem present .venv is a working one.
set VENV_OK=0
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>&1
    if not errorlevel 1 set VENV_OK=1
)

if "!VENV_OK!"=="0" (
    echo Setting up ClinicEval for this computer - this only happens once...
    echo.

    where py >nul 2>&1
    if not errorlevel 1 (
        set PY_LAUNCHER=py
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            set PY_LAUNCHER=python
        ) else (
            echo ERROR: No Python installation was found on this computer.
            echo.
            echo Install Python 3 from https://www.python.org/downloads/
            echo and make sure "Add Python to PATH" is checked during setup,
            echo then run this file again.
            echo.
            pause
            exit /b 1
        )
    )

    if exist ".venv" (
        echo Removing an incompatible .venv from another computer...
        rmdir /s /q ".venv"
    )

    echo Creating a virtual environment...
    !PY_LAUNCHER! -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )

    echo Installing dependencies...
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies. Check your internet connection.
        pause
        exit /b 1
    )

    echo Setup complete.
    echo.
)

".venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo ClinicEval exited with an error - see above.
    pause
)

endlocal

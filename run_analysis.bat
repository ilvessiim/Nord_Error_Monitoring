@echo off
cd /d "%~dp0"
echo === TELEMEETRIA ANALUUSI KAIVITAMINE ===
where python3 >nul 2>nul
if %errorlevel% equ 0 (
    python3 analyze_telemetry.py
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python analyze_telemetry.py
    ) else (
        echo Viga: Python ei ole installitud voi kattesaadav.
    )
)
echo.
echo Protsess lopetas too.
pause

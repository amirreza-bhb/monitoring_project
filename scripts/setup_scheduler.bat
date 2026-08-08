@echo off
setlocal

REM ============================================================
REM Project paths
REM ============================================================

set "SCRIPTS_DIR=%~dp0"

set "INFLATION_BAT=%SCRIPTS_DIR%run_inflation_etl.bat"
set "MARKET_BAT=%SCRIPTS_DIR%run_market_etl.bat"

REM ============================================================
REM Task names
REM ============================================================

set "INFLATION_TASK=ETL - Inflation monthly"
set "MARKET_TASK=ETL - Market daily"

REM ============================================================
REM Create / update Inflation Task
REM ============================================================

echo.
echo Creating Inflation ETL task...

schtasks /create ^
 /tn "%INFLATION_TASK%" ^
 /tr "\"%INFLATION_BAT%\"" ^
 /sc monthly ^
 /mo 1 ^
 /d 1 ^
 /st 09:00 ^
 /f

if errorlevel 1 (
    echo Failed to create Inflation ETL task.
    goto :error
)

REM ============================================================
REM Create / update Market Task
REM ============================================================

echo.
echo Creating Market ETL task...

schtasks /create ^
 /tn "%MARKET_TASK%" ^
 /tr "\"%MARKET_BAT%\"" ^
 /sc daily ^
 /st 08:30 ^
 /f

if errorlevel 1 (
    echo Failed to create Market ETL task.
    goto :error
)

echo.
echo ============================================================
echo Task Scheduler setup completed successfully.
echo ============================================================
echo.
echo Inflation task:
echo   %INFLATION_TASK%
echo.
echo Market task:
echo   %MARKET_TASK%
echo.

pause
exit /b 0

:error

echo.
echo ============================================================
echo Task Scheduler setup FAILED.
echo ============================================================
echo.
pause
exit /b 1
@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" "etl\market_data_etl.py"
@echo off

cd /d "%~dp0.."

".venv\Scripts\python.exe" "etl\inflation_data_etl.py"
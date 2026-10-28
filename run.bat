@echo off
cd /d "%~dp0"
echo Starting WARDHAN TRADING EST. Quotation Generator...
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause

@echo off
echo ============================================
echo   Dark Pattern Detector - Backend Server
echo ============================================
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0"
python app.py
pause

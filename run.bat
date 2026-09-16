@echo off
title Asmary Tender Intelligence Web App
echo ========================================================
echo   Asmary Field Services - Upstream Tender Dashboard
echo ========================================================
echo.
echo Installing/Verifying dependencies...
pip install -r requirements.txt
echo.
echo Starting Local Web Server on http://localhost:5000...
echo Open your browser and visit: http://localhost:5000
echo.
python app.py
pause

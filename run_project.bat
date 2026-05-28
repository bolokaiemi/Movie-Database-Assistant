@echo off
chcp 65001 > nul
title 🎬 Stoplight Cinema Portal Launcher
echo =================================================================
echo        STOPLIGHT PUBLIC CINEMA & ANALYTICS LAUNCHER
echo =================================================================
echo.

echo 🚀 Launching Flask Web Server in a new window...
start "🎬 Flask Web Server" cmd /k "chcp 65001 > nul && cd /d %~dp0 && .\.venv\Scripts\python app.py"

echo.
echo 🚀 Launching Streamlit Analytics Server in a new window...
start "📊 Streamlit Analytics Dashboard" cmd /k "chcp 65001 > nul && cd /d %~dp0 && .\.venv\Scripts\streamlit run analytic.py --server.enableCORS=false --server.enableXsrfProtection=false"

echo.
echo =================================================================
echo ✅ SUCCESS: Both servers are launching in separate windows!
echo.
echo 🔗 Flask Web App:       http://127.0.0.1:5000
echo 🔗 Analytics Dashboard: http://127.0.0.1:8501
echo.
echo Please leave both command windows open during your presentation.
echo =================================================================
echo.
pause

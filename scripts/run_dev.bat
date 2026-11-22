@echo off
TITLE Antigravity Multimodal AI Companion Launcher
echo ===================================================
echo   Starting Multimodal AI Companion MVP
echo ===================================================

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Backend (FastAPI)" cmd /k "python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Streamlit Frontend on http://localhost:8501 ...
start "Frontend (Streamlit)" cmd /k "python -m streamlit run app/frontend/streamlit_app.py --server.port 8501"

echo.
echo ===================================================
echo   System running!
echo   - Backend Docs:  http://127.0.0.1:8000/docs
echo   - Frontend UI:   http://localhost:8501
echo ===================================================

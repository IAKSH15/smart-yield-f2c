@echo off
echo ========================================================
echo   Smart-Yield F2C - Starting Complete Prototype
echo ========================================================

echo.
echo [1/3] Checking and Installing Python Dependencies...
pip install -r requirements.txt

echo.
echo [2/3] Checking and Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo [3/3] Launching Backend and Frontend Servers...
start "Smart-Yield Backend (FastAPI)" cmd /k "python -m uvicorn backend.main:app --port 8000 --reload"
timeout /t 3 /nobreak >nul

cd frontend
start "Smart-Yield Frontend (React)" cmd /k "npm run dev -- --port 5173"
cd ..

timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo ========================================================
echo   Smart-Yield F2C is Running!
echo   Frontend: http://localhost:5173
echo   Backend Docs: http://127.0.0.1:8000/docs
echo ========================================================
pause

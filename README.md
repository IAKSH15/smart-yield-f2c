# Smart-Yield F2C — Quick Setup & Run Guide

To run this complete working prototype on any other laptop (Windows / Mac / Linux), follow these simple steps:

---

## 1. Prerequisites (Must be installed on the laptop)
1. **Python 3.10+**: [python.org](https://www.python.org/downloads/) *(During installation, make sure to check **"Add Python to PATH"**)*.
2. **Node.js 18+ & npm**: [nodejs.org](https://nodejs.org/)

---

## 2. Option A: 1-Click Launch (Windows)
If your friend is on Windows:
1. Double-click the file:
   ```text
   run_app.bat
   ```
2. It will automatically:
   - Install required Python dependencies (`requirements.txt`).
   - Install required React frontend dependencies (`npm install`).
   - Launch the FastAPI backend on `http://127.0.0.1:8000`.
   - Launch the React frontend on `http://localhost:5173`.
   - Automatically open the web browser.

---

## 3. Option B: Manual Terminal Launch (Windows / Mac / Linux)

### Terminal 1 — Start the Backend
Open a terminal in the project root folder (`SIH_AG_PR`):
```bash
# 1. Install backend dependencies
pip install -r requirements.txt

# 2. Run backend server
python -m uvicorn backend.main:app --port 8000 --reload
```
*Backend will be running at:* `http://127.0.0.1:8000`  
*API Swagger Documentation:* `http://127.0.0.1:8000/docs`

---

### Terminal 2 — Start the Frontend
Open a second terminal and navigate to the `frontend` folder:
```bash
cd frontend

# 1. Install frontend dependencies
npm install

# 2. Run React development server
npm run dev -- --port 5173
```
*Frontend will be running at:* `http://localhost:5173`

---

## 4. Run Automated Test Suite
To verify that all Section 8 formulas, pricing engine, bid acceptance/rejection, and escrow flows work properly:
```bash
python test_suite.py
```
Expected output:
```text
===> ALL 7 BACKEND END-TO-END FLOW TESTS COMPLETED SUCCESSFULLY! <===
```

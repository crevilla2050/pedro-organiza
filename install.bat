@echo off
echo === Pedro Organiza Installer ===

REM -------------------------------
REM 1. Python check
REM -------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found.
  echo Please install Python 3.9+ from https://www.python.org
  pause
  exit /b 1
)

echo [OK] Python found

REM -------------------------------
REM 2. Virtual environment
REM -------------------------------
if not exist venv (
  echo [INFO] Creating virtual environment...
  python -m venv venv
)

REM -------------------------------
REM 3. Activate venv
REM -------------------------------
call venv\Scripts\activate

REM -------------------------------
REM 4. Upgrade core tooling
REM -------------------------------
python -m pip install --upgrade pip setuptools wheel

REM -------------------------------
REM 5. Install Pedro + dependencies
REM -------------------------------
echo [INFO] Installing Pedro Organiza and dependencies...
pip install .

REM -------------------------------
REM 6. Sanity checks (non-fatal)
REM -------------------------------
echo.
echo [INFO] Performing sanity checks...

python - <<EOF
try:
    import fastapi, uvicorn, dotenv, pydantic
    print("[OK] API dependencies present")
except Exception as e:
    print("[WARN] API dependency issue:", e)
EOF

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [WARN] ffmpeg not found (optional, required for fingerprinting)
)

REM -------------------------------
REM Done
REM -------------------------------
echo.
echo === Installation complete ===
echo.
echo Activate with:
echo   venv\Scripts\activate
echo.
echo Try:
echo   pedro status
pause
exit /b 0

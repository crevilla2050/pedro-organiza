@echo off
setlocal ENABLEDELAYEDEXPANSION

echo === Pedro Organiza Installer ===
echo.

REM -------------------------------
REM 1. Python check + version
REM -------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found.
  echo Please install Python 3.9+ from https://www.python.org
  pause
  exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
echo [OK] Python found: %PYVER%

REM crude version check (3.9+)
python - <<EOF
import sys
if sys.version_info < (3,9):
    raise SystemExit("Python 3.9+ required")
EOF

if errorlevel 1 (
  echo [ERROR] Python 3.9 or newer is required.
  pause
  exit /b 1
)

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
REM 5. Install Pedro (editable)
REM -------------------------------
echo [INFO] Installing Pedro Organiza (editable)...
pip install -e .

if errorlevel 1 (
  echo [ERROR] Pedro installation failed.
  pause
  exit /b 1
)

REM -------------------------------
REM 6. Ensure config.json exists
REM -------------------------------
if not exist backend\config.json (
  echo [INFO] Initializing Pedro config...
  pedro init --force
)

REM -------------------------------
REM 7. UI dependencies (optional)
REM -------------------------------
where node >nul 2>nul
if errorlevel 1 (
  echo [WARN] Node.js not found.
  echo UI will not run until Node.js 18+ is installed.
) else (
  echo [OK] Node.js found
  if exist music-ui\package.json (
    echo [INFO] Installing UI dependencies...
    pushd music-ui
    npm install
    popd
  )
)

REM -------------------------------
REM 8. Sanity checks (non-fatal)
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
echo   pedro scan
echo.
pause
exit /b 0

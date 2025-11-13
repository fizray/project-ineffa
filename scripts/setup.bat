@echo off
REM Quick Setup Script untuk Face Attendance PoC
REM Untuk Windows dengan NVIDIA GPU

echo ================================================
echo Face Attendance PoC - Quick Setup
echo ================================================
echo.

REM Check if running from correct directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please run this script from project directory
    pause
    exit /b 1
)

echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9-3.11 from https://www.python.org
    pause
    exit /b 1
)

echo OK - Python found
python --version

echo.
echo [2/4] Checking NVIDIA GPU...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo WARNING: NVIDIA GPU not detected
    echo Will setup for CPU mode
    set GPU_MODE=cpu
) else (
    echo OK - NVIDIA GPU detected
    nvidia-smi --query-gpu=name --format=csv,noheader
    set GPU_MODE=gpu
)

echo.
echo [3/4] Running PowerShell setup script...
echo This may take 5-10 minutes...
echo.

powershell -ExecutionPolicy Bypass -File setup_gpu_windows.ps1

if errorlevel 1 (
    echo.
    echo ERROR: Setup failed!
    echo Please check error messages above
    pause
    exit /b 1
)

echo.
echo [4/4] Setup completed!
echo.
echo ================================================
echo Next Steps:
echo ================================================
echo.
echo 1. Activate virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 2. Run the application:
echo    python main.py
echo.
echo 3. Enroll users:
echo    python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20
echo.
echo For more help, see QUICK_START_ID.md
echo ================================================
echo.

pause

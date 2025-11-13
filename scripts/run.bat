@echo off
REM Quick Run Script untuk Face Attendance PoC

echo ================================================
echo Face Attendance PoC - Quick Run
echo ================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found!
    pause
    exit /b 1
)

echo.
echo ================================================
echo Starting Face Attendance System...
echo ================================================
echo.
echo Press Ctrl+C to stop
echo.

REM Run the application
python main.py

REM Deactivate on exit
deactivate

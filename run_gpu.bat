@echo off
set CONDA_PATH=C:\Users\fiz\miniconda3
set ENV_NAME=ineffa-gpu

echo Activating Conda Environment: %ENV_NAME%...
call "%CONDA_PATH%\Scripts\activate.bat" %ENV_NAME%

if errorlevel 1 (
    echo Failed to activate conda environment.
    pause
    exit /b 1
)

echo Launching Face Attendance System...
python launch.py

pause

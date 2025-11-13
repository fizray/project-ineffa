@echo off
REM Quick Enrollment Script

echo ================================================
echo Face Attendance PoC - User Enrollment
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
call venv\Scripts\activate.bat

echo Enter user details:
echo.

REM Get user input
set /p USER_ID="User ID (e.g., emp001): "
set /p USER_NAME="User Name (e.g., John Doe): "
set /p NUM_IMAGES="Number of images (default 20): "

if "%NUM_IMAGES%"=="" set NUM_IMAGES=20

echo.
echo ================================================
echo Enrolling User
echo ================================================
echo User ID: %USER_ID%
echo Name: %USER_NAME%
echo Images: %NUM_IMAGES%
echo ================================================
echo.
echo Please look at the camera when prompted
echo Move your head slightly for better coverage
echo.

REM Run enrollment
python enrollment_tool.py --mode realtime --user-id "%USER_ID%" --user-name "%USER_NAME%" --num-images %NUM_IMAGES%

if errorlevel 1 (
    echo.
    echo ERROR: Enrollment failed!
    pause
) else (
    echo.
    echo SUCCESS: User enrolled successfully!
    echo.
    pause
)

deactivate

import os
import sys
import subprocess
import time
import shutil

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("\033[96m==================================================\033[0m")
    print("\033[1m          FACE ATTENDANCE SYSTEM LAUNCHER         \033[0m")
    print("\033[96m==================================================\033[0m")

def run_conda_setup():
    print("\n\033[93m[INFO] Starting Conda GPU Setup...\033[0m")
    script_path = os.path.join("scripts", "setup_conda_gpu.ps1")
    if os.path.exists(script_path):
        try:
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], check=True)
        except Exception as e:
            print(f"\033[91mFailed to run setup script: {e}\033[0m")
    else:
        print("\033[91mSetup script not found!\033[0m")
    input("\nPress Enter to return to menu...")

def set_conda_path_and_activate(interactive=True):
    """Ask user for conda base path, add to PATH for this process, and set LAUNCHER_PYTHON to env python if exists."""
    if interactive:
        print("\n\033[93m[INFO] Configure Conda path and activate 'ineffa-gpu' for this launcher session\033[0m")
        default_path = r"C:\Users\fiz\miniconda3"
        conda_base = input(f"Conda base path [{default_path}]: ").strip() or default_path
    else:
        # Auto-detect or use default
        conda_base = r"C:\Users\fiz\miniconda3"
        if not os.path.exists(conda_base):
            # Try to find it in common locations or env var
            pass

    condabin = os.path.join(conda_base, "condabin")
    conda_python = os.path.join(conda_base, "envs", "ineffa-gpu", "python.exe")

    if not os.path.exists(condabin):
        if interactive:
            print(f"\033[91mcondabin not found at {condabin}. Make sure path is correct.\033[0m")
            input("\nPress Enter to return to menu...")
        return

    # Prepend to PATH for this process only
    os.environ['PATH'] = condabin + os.pathsep + os.environ.get('PATH', '')
    if interactive:
        print(f"\033[92mTemporarily added {condabin} to PATH for this session.\033[0m")

    if os.path.exists(conda_python):
        globals()['LAUNCHER_PYTHON'] = conda_python
        if interactive:
            print(f"\033[92mFound 'ineffa-gpu' python at {conda_python}. Launcher will use it for commands.\033[0m")
        
        # Add Library/bin to PATH for CUDA DLLs
        conda_lib_bin = os.path.join(conda_base, "envs", "ineffa-gpu", "Library", "bin")
        if os.path.exists(conda_lib_bin):
            os.environ['PATH'] = conda_lib_bin + os.pathsep + os.environ.get('PATH', '')
            if interactive:
                print(f"\033[92mAdded {conda_lib_bin} to PATH for CUDA DLLs.\033[0m")
        
        # Also add Library/lib just in case
        conda_lib_lib = os.path.join(conda_base, "envs", "ineffa-gpu", "Library", "lib")
        if os.path.exists(conda_lib_lib):
            os.environ['PATH'] = conda_lib_lib + os.pathsep + os.environ.get('PATH', '')

        # Also add the root of the env
        conda_env_root = os.path.join(conda_base, "envs", "ineffa-gpu")
        os.environ['PATH'] = conda_env_root + os.pathsep + os.environ.get('PATH', '')

        # Also add Scripts
        conda_scripts = os.path.join(conda_base, "envs", "ineffa-gpu", "Scripts")
        if os.path.exists(conda_scripts):
            os.environ['PATH'] = conda_scripts + os.pathsep + os.environ.get('PATH', '')
        
        # Force CUDA provider for ONNX Runtime
        os.environ['ORT_CUDA_PROVIDER_OPTIONS'] = 'device_id=0'
        
        # Optionally verify by printing version
        try:
            if interactive:
                subprocess.run([conda_python, "--version"], check=False)
        except Exception:
            pass
    else:
        if interactive:
            print(f"\033[93m'ineffa-gpu' environment not found at {conda_python}. You can still use 'conda run' in scripts.\033[0m")

    if interactive:
        input("\nPress Enter to return to menu...")

def run_enrollment():
    print("\n\033[93m[INFO] Starting Enrollment Tool...\033[0m")
    
    # Auto-activate if not already set
    if 'LAUNCHER_PYTHON' not in globals():
        print("\033[90mAuto-activating Conda environment...\033[0m")
        set_conda_path_and_activate(interactive=False)

    # Get user input
    print("\nPlease provide user details:")
    user_id = input("  Enter User ID (e.g., 001): ").strip()
    if not user_id:
        print("\033[91m  Error: User ID is required!\033[0m")
        input("\nPress Enter to return to menu...")
        return

    user_name = input("  Enter User Name: ").strip()
    if not user_name:
        print("\033[91m  Error: User Name is required!\033[0m")
        input("\nPress Enter to return to menu...")
        return
        
    try:
        python_exec = globals().get('LAUNCHER_PYTHON', sys.executable)
        subprocess.run([python_exec, "enrollment_tool.py", "--id", user_id, "--name", user_name], check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        print(f"\n\033[91m[ERROR] Enrollment tool crashed with code {e.returncode}\033[0m")
    input("\nPress Enter to return to menu...")

def run_verification():
    print("\n\033[93m[INFO] Verifying System Status...\033[0m")
    
    # Auto-activate if not already set
    if 'LAUNCHER_PYTHON' not in globals():
        print("\033[90mAuto-activating Conda environment...\033[0m")
        set_conda_path_and_activate(interactive=False)
        
    python_exec = globals().get('LAUNCHER_PYTHON', sys.executable)
    
    print(f"Using Python: {python_exec}")
    
    # Check imports
    imports = ["cv2", "numpy", "onnxruntime", "yaml"]
    print("\nChecking dependencies:")
    for imp in imports:
        try:
            subprocess.run([python_exec, "-c", f"import {imp}; print('  [OK] {imp}')"], check=True)
        except subprocess.CalledProcessError:
            print(f"  [FAIL] {imp}")
            
    # Check GPU
    print("\nChecking GPU availability (ONNX Runtime):")
    try:
        cmd = "import onnxruntime as ort; print(f'  Providers: {ort.get_available_providers()}')"
        subprocess.run([python_exec, "-c", cmd], check=True)
    except subprocess.CalledProcessError:
        print("  [FAIL] Could not check ONNX Runtime")

    input("\nPress Enter to return to menu...")

def run_attendance():
    print("\n\033[93m[INFO] Starting Attendance System...\033[0m")
    
    # Auto-activate if not already set
    if 'LAUNCHER_PYTHON' not in globals():
        print("\033[90mAuto-activating Conda environment...\033[0m")
        set_conda_path_and_activate(interactive=False)
        
    try:
        # If a conda env has been activated via launcher, prefer its python
        python_exec = globals().get('LAUNCHER_PYTHON', sys.executable)
        subprocess.run([python_exec, "main.py"], check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        print(f"\n\033[91m[ERROR] System crashed with code {e.returncode}\033[0m")
    input("\nPress Enter to return to menu...")

def check_cameras():
    print("\n\033[93m[INFO] Scanning for connected cameras...\033[0m")
    
    # Auto-activate if not already set
    if 'LAUNCHER_PYTHON' not in globals():
        print("\033[90mAuto-activating Conda environment...\033[0m")
        set_conda_path_and_activate(interactive=False)
        
    python_exec = globals().get('LAUNCHER_PYTHON', sys.executable)
    
    # Python script to run inside the environment
    script = """
import cv2
import os

# Suppress OpenCV logs
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

print(f"\\n{'ID':<5} {'Status':<10} {'Resolution'}")
print("-" * 30)

found = False
# Check first 5 indices
for i in range(5):
    # On Windows, CAP_DSHOW (700) is often faster for checking
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(i)
        
    if cap.isOpened():
        found = True
        w = int(cap.get(3)) # CAP_PROP_FRAME_WIDTH
        h = int(cap.get(4)) # CAP_PROP_FRAME_HEIGHT
        print(f"{i:<5} {'Online':<10} {w}x{h}")
        cap.release()
        
if not found:
    print("No cameras detected.")
"""
    try:
        subprocess.run([python_exec, "-c", script], check=True)
    except subprocess.CalledProcessError:
        print("\033[91mFailed to scan cameras.\033[0m")
        
    input("\nPress Enter to return to menu...")

def clean_logs():
    confirm = input("\n\033[91mAre you sure you want to clear attendance logs? (y/n): \033[0m")
    if confirm.lower() == 'y':
        log_path = os.path.join("data", "attendance.csv")
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
                print("\033[92mLogs cleared successfully.\033[0m")
            except Exception as e:
                print(f"\033[91mError: {e}\033[0m")
        else:
            print("No logs found.")
    time.sleep(1)

def main():
    while True:
        clear_screen()
        print_header()
        print("1. \033[92mStart Attendance System\033[0m")
        print("2. \033[93mEnroll New User\033[0m")
        print("3. \033[94mVerify System Status\033[0m")
        print("4. \033[95mSetup Conda Environment (GPU)\033[0m")
        print("5. \033[96mSet Conda PATH & Activate 'ineffa-gpu' (session)\033[0m")
        print("6. \033[90mClear Attendance Logs\033[0m")
        print("7. \033[95mCheck Connected Cameras\033[0m")
        print("0. Exit")
        print("\033[96m==================================================\033[0m")
        
        try:
            choice = input("Select option: ").strip()
        except EOFError:
            print("\nNo input available. Exiting launcher.")
            sys.exit(0)
        
        if choice == '1':
            run_attendance()
        elif choice == '2':
            run_enrollment()
        elif choice == '3':
            run_verification()
        elif choice == '4':
            run_conda_setup()
        elif choice == '5':
            set_conda_path_and_activate()
        elif choice == '6':
            clean_logs()
        elif choice == '7':
            check_cameras()
        elif choice == '0':
            print("\nGoodbye!")
            sys.exit(0)
        else:
            print("\nInvalid option!")
            time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)

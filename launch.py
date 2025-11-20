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

def run_attendance():
    print("\n\033[93m[INFO] Starting Attendance System...\033[0m")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        print(f"\n\033[91m[ERROR] System crashed with code {e.returncode}\033[0m")
    input("\nPress Enter to return to menu...")

def run_enrollment():
    print("\n\033[93m[INFO] New User Enrollment\033[0m")
    user_id = input("Enter User ID (e.g., 1001): ").strip()
    if not user_id:
        print("\033[91mID cannot be empty!\033[0m")
        time.sleep(1)
        return

    name = input("Enter Full Name: ").strip()
    if not name:
        print("\033[91mName cannot be empty!\033[0m")
        time.sleep(1)
        return

    try:
        samples = input("Number of samples (default 5): ").strip()
        samples = int(samples) if samples.isdigit() else 5
        
        cmd = [sys.executable, "enrollment_tool.py", "--id", user_id, "--name", name, "--samples", str(samples)]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError:
        print("\n\033[91m[ERROR] Enrollment failed.\033[0m")
    
    input("\nPress Enter to return to menu...")

def run_verification():
    print("\n\033[93m[INFO] Running System Verification...\033[0m")
    script_path = os.path.join("scripts", "verify_setup.ps1")
    if os.path.exists(script_path):
        try:
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], check=True)
        except Exception as e:
            print(f"\033[91mFailed to run verification script: {e}\033[0m")
    else:
        print("\033[91mVerification script not found!\033[0m")
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
        print("4. \033[90mClear Attendance Logs\033[0m")
        print("0. Exit")
        print("\033[96m==================================================\033[0m")
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            run_attendance()
        elif choice == '2':
            run_enrollment()
        elif choice == '3':
            run_verification()
        elif choice == '4':
            clean_logs()
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

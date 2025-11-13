#!/usr/bin/env python3
"""
Setup script for Face Recognition Attendance PoC
This script helps users set up the system and verify dependencies
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version)
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def check_dependencies():
    """Check if all dependencies can be imported"""
    print("\\n🔍 Checking dependencies...")
    
    dependencies = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('yaml', 'PyYAML'),
        ('torch', 'torch'),
        ('PIL', 'Pillow'),
        ('mtcnn', 'mtcnn')
    ]
    
    missing = []
    for module, package in dependencies:
        try:
            importlib.import_module(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    return len(missing) == 0

def create_directories():
    """Create necessary directories"""
    print("\\n📁 Creating directories...")
    
    directories = ['gallery', 'snapshots']
    
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created: {dir_name}/")
    
    return True

def check_camera():
    """Check if camera is available"""
    print("\\n📷 Checking camera...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            print("✅ Camera detected")
            return True
        else:
            print("❌ Camera not accessible")
            return False
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def create_config():
    """Create default configuration if not exists"""
    print("\\n⚙️  Checking configuration...")
    
    if not os.path.exists('config.yaml'):
        print("❌ config.yaml not found")
        return False
    else:
        print("✅ Configuration file found")
        return True

def run_test():
    """Run a simple test"""
    print("\\n🧪 Running system test...")
    
    try:
        # Test basic imports
        from face_detection import FaceDetector
        from matching_engine import MatchingEngine, EmbeddingManager
        
        # Test component initialization
        detector = FaceDetector()
        manager = EmbeddingManager()
        engine = MatchingEngine(manager)
        
        print("✅ All components initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Face Recognition Attendance PoC Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Checking dependencies", check_dependencies),
        ("Creating directories", create_directories),
        ("Checking camera", check_camera),
        ("Checking configuration", create_config),
        ("Running test", run_test)
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            results.append(False)
    
    print("\\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    for i, (step_name, _) in enumerate(steps):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{step_name:<30} {status}")
    
    print(f"\\nOverall: {success_count}/{total_count} steps completed")
    
    if success_count == total_count:
        print("\\n🎉 Setup completed successfully!")
        print("\\n📖 Next steps:")
        print("1. Review and edit config.yaml if needed")
        print("2. Run: python main.py")
        print("3. For enrollment: python enrollment_tool.py --mode realtime --user-id user_001 --user-name 'Your Name'")
        print("\\n📖 Read README.md for detailed instructions")
    else:
        print("\\n⚠️  Setup incomplete. Please fix the issues above.")
        print("\\n🆘 Troubleshooting:")
        print("1. Make sure Python 3.9+ is installed")
        print("2. Install dependencies manually: pip install -r requirements.txt")
        print("3. Check camera permissions and availability")
        print("4. Ensure you have sufficient system resources")

if __name__ == "__main__":
    main()
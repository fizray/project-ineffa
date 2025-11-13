# 📝 Command Cheatsheet - Face Attendance PoC

Quick reference untuk command yang sering dipakai.

## 🚀 Setup & Installation

```powershell
# Setup otomatis (Windows + GPU)
.\setup_gpu_windows.ps1

# Verifikasi setup
.\verify_setup.ps1

# Aktifkan virtual environment
.\venv\Scripts\Activate.ps1

# Manual install PyTorch + CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Manual install PyTorch + CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## 🎮 Running Application

```powershell
# Jalankan aplikasi utama
python main.py

# Dengan custom config
python main.py custom_config.yaml
```

## 👥 User Enrollment

```powershell
# Enroll user baru (real-time dari camera)
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20

# Enroll dari folder images
python enrollment_tool.py --mode batch --user-id emp002 --user-name "Jane Smith" --image-dir ./user_photos

# List semua users
python enrollment_tool.py --mode list

# Remove user
python enrollment_tool.py --mode remove --user-id emp001

# Export user data
python enrollment_tool.py --mode export --output users_backup.json
```

## 🧪 Testing & Benchmarking

```powershell
# Compare GPU vs CPU performance
python benchmark_gpu.py --mode compare

# Benchmark GPU only
python benchmark_gpu.py --mode gpu --iterations 100

# Benchmark CPU only
python benchmark_gpu.py --mode cpu --iterations 100

# Benchmark full pipeline dengan camera
python benchmark_gpu.py --mode pipeline --duration 30

# Generate performance report
python testing_tool.py --mode report --output performance_report.html

# Analyze attendance logs
python testing_tool.py --mode analyze --log-path attendance.csv

# Calibrate matching threshold
python testing_tool.py --mode calibrate --target-far 0.01

# Export test results
python testing_tool.py --mode export --output test_results.json
```

## 🔍 Diagnostics

```powershell
# Check Python version
python --version

# Check PyTorch & CUDA
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Check GPU info
nvidia-smi

# Monitor GPU real-time (update setiap 1 detik)
nvidia-smi -l 1

# Check CUDA version
nvcc --version

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera:', 'OK' if cap.isOpened() else 'FAIL'); cap.release()"

# Test embedding extractor
python -c "from embedding_extractor import EmbeddingExtractor; e = EmbeddingExtractor(config={'enable_gpu': True}); print(e.get_model_info())"

# Check all dependencies
pip list

# Test individual components
python face_detection.py
python embedding_extractor.py
python matching_engine.py
```

## ⚙️ Configuration

```powershell
# Edit config file
notepad config.yaml

# Backup config
Copy-Item config.yaml config.yaml.backup

# Restore config
Copy-Item config.yaml.backup config.yaml
```

### Common Config Tweaks

```yaml
# Enable/Disable GPU
enable_gpu: true                # true = GPU, false = CPU

# GPU Memory (adjust jika out of memory)
gpu_memory_fraction: 0.8        # 0.5 = 50%, 0.8 = 80%, 1.0 = 100%

# Performance (tuning untuk FPS)
grab_every_n_frames: 5          # Lebih tinggi = lebih cepat, kurang smooth
                                # 3-5 untuk GPU, 7-10 untuk CPU

# Camera resolution (tuning untuk performance)
frame_width: 1280               # 640 = fast, 1280 = normal, 1920 = high quality
frame_height: 720               # 480 = fast, 720 = normal, 1080 = high quality

# Camera ID (jika punya multiple cameras)
camera_id: 0                    # 0 = default, 1 = second camera, dst.

# Recognition threshold (tuning untuk accuracy)
threshold_match: 0.62           # 0.5 = loose, 0.7 = normal, 0.9 = strict

# Attendance cooldown
attendance_cooldown: 30         # Seconds antara recording untuk user yang sama
```

## 📊 Data Management

```powershell
# View attendance log
Get-Content attendance.csv | Select-Object -Last 20

# Count attendance records
(Get-Content attendance.csv | Measure-Object -Line).Lines - 1

# Backup embeddings
Copy-Item embeddings.json embeddings.json.backup

# Clear attendance log (hati-hati!)
Remove-Item attendance.csv

# Clear snapshots
Remove-Item snapshots\* -Recurse

# List enrolled users
python -c "from embedding_extractor import EmbeddingManager; m = EmbeddingManager(); print('\n'.join(m.list_users()))"
```

## 🎯 Keyboard Controls (saat aplikasi running)

| Key | Action |
|-----|--------|
| `Q` | Quit aplikasi |
| `E` | Start enrollment mode |
| `S` | Save manual snapshot |
| `R` | Reset detection |
| `H` | Show help dialog |

## 🛠️ Troubleshooting Commands

```powershell
# GPU not detected - check driver
nvidia-smi

# Out of memory - check GPU usage
nvidia-smi

# Camera not working - try different index
python -c "import cv2; for i in range(5): cap = cv2.VideoCapture(i); print(f'Camera {i}:', 'OK' if cap.isOpened() else 'FAIL'); cap.release()"

# Reinstall PyTorch (if GPU not working)
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Reset virtual environment
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Clear pip cache
pip cache purge
```

## 📦 Package Management

```powershell
# Update pip
python -m pip install --upgrade pip

# Install from requirements
pip install -r requirements.txt

# Freeze current packages
pip freeze > requirements_freeze.txt

# Update specific package
pip install --upgrade numpy

# Uninstall package
pip uninstall package_name
```

## 🔐 Advanced

```powershell
# Enable debug mode (edit config.yaml)
# debug_mode: true

# Check process memory usage
Get-Process python | Select-Object Name, CPU, WorkingSet

# Kill all Python processes (jika stuck)
Get-Process python | Stop-Process -Force

# Set GPU to specific device (multi-GPU)
$env:CUDA_VISIBLE_DEVICES="0"  # Use GPU 0
python main.py

# Run with CPU only (even if GPU available)
$env:CUDA_VISIBLE_DEVICES="-1"
python main.py
```

## 📈 Performance Monitoring

```powershell
# Real-time GPU monitoring
nvidia-smi -l 1

# GPU utilization only
nvidia-smi --query-gpu=utilization.gpu --format=csv -l 1

# GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv -l 1

# Application FPS (check logs saat running)
Get-Content attendance.csv | Select-Object -Last 1

# Windows Task Manager
taskmgr
# Lihat tab "Performance" > GPU
```

## 🔄 Update & Maintenance

```powershell
# Pull latest code (if using git)
git pull origin master

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Clean Python cache
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse

# Backup everything
$date = Get-Date -Format "yyyyMMdd"
Compress-Archive -Path * -DestinationPath "backup_$date.zip"
```

## 📚 Quick Links

- **Setup Guide**: `SETUP_WINDOWS_GPU.md`
- **Quick Start**: `QUICK_START_ID.md`
- **Full Documentation**: `README.md`
- **Technical Docs**: `ai_face_attendance_poc.md`

## 💡 Tips

1. **Untuk performance terbaik**: Enable GPU, pakai resolusi 1280x720, set `grab_every_n_frames: 3`
2. **Untuk stability**: Disable GPU jika sering crash, pakai resolusi 640x480
3. **Untuk accuracy**: Enroll minimal 20 images per user, dengan variasi angle & lighting
4. **Untuk debugging**: Enable `debug_mode: true` dan check attendance.csv
5. **Untuk multi-camera**: Set `camera_id` yang sesuai di config.yaml

## ⚡ One-Liners

```powershell
# Setup + Run dalam satu command
.\setup_gpu_windows.ps1; .\venv\Scripts\Activate.ps1; python main.py

# Quick GPU check
python -c "import torch; print('GPU OK' if torch.cuda.is_available() else 'No GPU')"

# Quick benchmark
python benchmark_gpu.py --mode compare --iterations 20

# List enrolled users dengan count
python -c "from embedding_extractor import EmbeddingManager; m = EmbeddingManager(); users = m.list_users(); print(f'Total users: {len(users)}'); [print(f'  - {u}') for u in users]"

# Tail attendance log
Get-Content attendance.csv -Wait -Tail 10
```

---

**Save this file untuk quick reference! 🚀**

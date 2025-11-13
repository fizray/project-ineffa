# 🚀 Quick Start - Face Attendance PoC (Windows + GPU)

Panduan cepat setup aplikasi Face Recognition Attendance di Windows dengan GPU acceleration.

## 📋 Prerequisites

**Hardware:**
- NVIDIA GPU (GTX 1050 atau lebih tinggi)
- Webcam (USB atau built-in)
- RAM minimal 4GB

**Software:**
- Windows 10/11 (64-bit)
- Python 3.9-3.11
- NVIDIA Driver terbaru
- CUDA Toolkit 11.8 atau 12.1

## ⚡ Setup Otomatis (Recommended)

### 1. Clone/Download Project

```powershell
cd E:\project-ineffa
```

### 2. Jalankan Setup Script

```powershell
# Jalankan PowerShell sebagai Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Jalankan setup
.\setup_gpu_windows.ps1
```

Script ini akan otomatis:
- ✅ Check prerequisites (Python, GPU, CUDA)
- ✅ Buat virtual environment
- ✅ Install PyTorch dengan CUDA support
- ✅ Install semua dependencies
- ✅ Verifikasi setup

### 3. Verifikasi Setup

```powershell
.\verify_setup.ps1
```

### 4. Jalankan Aplikasi

```powershell
# Aktifkan virtual environment
.\venv\Scripts\Activate.ps1

# Jalankan aplikasi
python main.py
```

## 🎯 Manual Setup

Jika setup otomatis gagal, ikuti langkah manual:

### 1. Install CUDA Toolkit

Download dan install: https://developer.nvidia.com/cuda-downloads

### 2. Setup Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 3. Install PyTorch dengan CUDA

**Untuk CUDA 11.8:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Untuk CUDA 12.1:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install Dependencies

```powershell
pip install numpy>=1.24,<2.0
pip install opencv-python>=4.7,<4.10
pip install facenet-pytorch>=2.5,<3.0
pip install scipy>=1.10,<1.13
pip install Pillow>=10.0,<11.0
pip install PyYAML>=6.0,<7.0
pip install pandas>=2.0,<2.3
pip install matplotlib>=3.7,<3.9
pip install seaborn>=0.12,<0.14
```

### 5. Verifikasi GPU

```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

## 📝 Penggunaan

### Jalankan Aplikasi

```powershell
# Aktifkan venv (jika belum)
.\venv\Scripts\Activate.ps1

# Jalankan
python main.py
```

### Keyboard Controls

| Key | Fungsi |
|-----|--------|
| `Q` | Quit aplikasi |
| `E` | Mulai enrollment mode |
| `S` | Save snapshot manual |
| `R` | Reset detection |
| `H` | Show help |

### Enroll User Baru

```powershell
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20
```

### List Users

```powershell
python enrollment_tool.py --mode list
```

### Remove User

```powershell
python enrollment_tool.py --mode remove --user-id emp001
```

### Testing & Analytics

```powershell
# Generate report
python testing_tool.py --mode report --output performance_report.html

# Analyze logs
python testing_tool.py --mode analyze --log-path attendance.csv
```

## ⚙️ Konfigurasi GPU

Edit `config.yaml`:

```yaml
# GPU Settings
enable_gpu: true              # Enable/disable GPU
gpu_memory_fraction: 0.8      # GPU memory usage (0.5 - 1.0)
prefer_gpu: true              # Prefer GPU over CPU
optimize_for_gpu: true        # GPU optimizations

# Performance Settings
grab_every_n_frames: 5        # Process setiap N frames
processing_batch_size: 1      # Batch size untuk GPU

# Camera Settings
camera_id: 0                  # Camera index (0, 1, 2, ...)
frame_width: 1280             # Resolution width
frame_height: 720             # Resolution height

# Recognition Settings
threshold_match: 0.62         # Matching threshold (0.5-0.9)
distance_metric: "cosine"     # Distance metric
```

## 🔧 Troubleshooting

### GPU Tidak Terdeteksi

1. Check NVIDIA driver:
```powershell
nvidia-smi
```

2. Check CUDA:
```powershell
nvcc --version
```

3. Reinstall PyTorch dengan CUDA

### Camera Tidak Terdeteksi

Coba camera index lain di `config.yaml`:
```yaml
camera_id: 1  # atau 2, 3, dst
```

Test manual:
```powershell
python -c "import cv2; cap = cv2.VideoCapture(1); print('OK' if cap.isOpened() else 'FAIL'); cap.release()"
```

### Out of Memory Error

Kurangi GPU memory usage di `config.yaml`:
```yaml
gpu_memory_fraction: 0.5
```

Atau kurangi resolusi:
```yaml
frame_width: 640
frame_height: 480
```

### Performance Lambat

1. Increase frame skip:
```yaml
grab_every_n_frames: 10
```

2. Enable optimizations:
```yaml
optimize_for_gpu: true
fast_preview: true
```

3. Tutup aplikasi lain yang pakai GPU

## 📊 Performance Benchmarks

| GPU | FPS (Detection) | FPS (Full Pipeline) |
|-----|-----------------|---------------------|
| CPU (i5) | ~5 FPS | ~3 FPS |
| GTX 1060 | ~15 FPS | ~12 FPS |
| RTX 3060 | ~30 FPS | ~25 FPS |
| RTX 4060 | ~50 FPS | ~40 FPS |

## 📚 Dokumentasi Lengkap

- **SETUP_WINDOWS_GPU.md** - Panduan setup detail
- **README.md** - Dokumentasi aplikasi lengkap
- **ai_face_attendance_poc.md** - Dokumentasi teknis

## 🆘 Support

Jika ada masalah:

1. Jalankan verifikasi: `.\verify_setup.ps1`
2. Baca SETUP_WINDOWS_GPU.md
3. Check logs di `attendance.csv`

## 📦 File Structure

```
project-ineffa/
├── main.py                      # Main application
├── config.yaml                  # Configuration
├── setup_gpu_windows.ps1        # Setup script
├── verify_setup.ps1             # Verification script
├── QUICK_START_ID.md           # This file
├── SETUP_WINDOWS_GPU.md        # Detail setup guide
├── face_detection.py            # Face detection
├── liveness_detection.py        # Liveness detection
├── embedding_extractor.py       # Embedding extraction (GPU)
├── matching_engine.py           # Face matching
├── logging_system.py            # Attendance logging
├── ui_system.py                # UI interface
├── enrollment_tool.py          # User enrollment
├── testing_tool.py             # Testing tools
├── requirements.txt            # Python dependencies
├── venv/                       # Virtual environment
├── gallery/                    # User images
├── snapshots/                  # Attendance snapshots
└── embeddings.json            # User embeddings
```

## 🎯 Quick Commands

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run app
python main.py

# Enroll user
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20

# List users
python enrollment_tool.py --mode list

# Verify GPU
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Monitor GPU
nvidia-smi -l 1

# Generate report
python testing_tool.py --mode report
```

## ✅ Checklist

- [ ] Python 3.9-3.11 installed
- [ ] NVIDIA Driver installed
- [ ] CUDA Toolkit installed
- [ ] Virtual environment created
- [ ] PyTorch with CUDA installed
- [ ] All dependencies installed
- [ ] GPU detected
- [ ] Camera working
- [ ] Application runs successfully

---

**Selamat menggunakan! 🎉**

Untuk pertanyaan lebih lanjut, baca dokumentasi lengkap di **SETUP_WINDOWS_GPU.md**

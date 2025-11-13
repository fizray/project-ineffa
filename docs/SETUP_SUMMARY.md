# Setup Summary - Face Attendance PoC (Windows + GPU)

## ✅ Apa yang Sudah Disiapkan

Saya sudah membuat setup lengkap untuk menjalankan aplikasi Face Recognition Attendance di Windows dengan GPU acceleration:

### 📝 File Setup yang Dibuat:

1. **`setup_gpu_windows.ps1`** - Script setup otomatis
   - Auto-detect GPU & CUDA
   - Install PyTorch dengan CUDA support
   - Install semua dependencies
   - Verifikasi setup

2. **`verify_setup.ps1`** - Script verifikasi setup
   - Check semua prerequisites
   - Test GPU acceleration
   - Test camera
   - Test semua dependencies

3. **`benchmark_gpu.py`** - Performance benchmark
   - Compare GPU vs CPU speed
   - Test embedding extraction
   - Test full pipeline

4. **`SETUP_WINDOWS_GPU.md`** - Panduan setup lengkap
   - Detail step-by-step installation
   - Troubleshooting guide
   - Configuration tips

5. **`QUICK_START_ID.md`** - Quick start guide (Bahasa Indonesia)
   - Setup cepat
   - Command reference
   - Troubleshooting

6. **`COMMANDS.md`** - Command cheatsheet
   - Semua command yang sering dipakai
   - Configuration tips
   - One-liner commands

## 🚀 Cara Setup (3 Langkah)

### Option A: Setup Otomatis (Recommended)

```powershell
# 1. Buka PowerShell di folder project
cd E:\project-ineffa

# 2. Jalankan setup script
.\setup_gpu_windows.ps1

# 3. Verifikasi
.\verify_setup.ps1
```

### Option B: Setup Manual

Lihat file `SETUP_WINDOWS_GPU.md` untuk panduan lengkap.

## 📋 Prerequisites

**Hardware:**
- ✅ NVIDIA GPU (GTX 1050+)
- ✅ Webcam
- ✅ 4GB+ RAM

**Software:**
- ✅ Windows 10/11 (64-bit)
- ✅ Python 3.9-3.11
- ✅ NVIDIA Driver
- ✅ CUDA Toolkit 11.8 atau 12.1

## 🎯 Quick Start

```powershell
# Aktifkan virtual environment
.\venv\Scripts\Activate.ps1

# Jalankan aplikasi
python main.py

# Enroll user pertama
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20
```

## 🔍 Verifikasi GPU

```powershell
# Check GPU tersedia
nvidia-smi

# Check PyTorch pakai GPU
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

# Test embedding extractor
python -c "from embedding_extractor import EmbeddingExtractor; e = EmbeddingExtractor(config={'enable_gpu': True}); print(e.get_model_info())"

# Benchmark performance
python benchmark_gpu.py --mode compare
```

## ⚙️ Konfigurasi GPU

File `config.yaml` sudah dikonfigurasi untuk GPU:

```yaml
# GPU Settings (sudah optimal)
enable_gpu: true                # Enable GPU acceleration
gpu_memory_fraction: 0.8        # Use 80% GPU memory
prefer_gpu: true                
optimize_for_gpu: true          

# Performance (adjust sesuai kebutuhan)
grab_every_n_frames: 5          # 3-5 untuk GPU, 7-10 untuk CPU
frame_width: 1280               # 640/1280/1920
frame_height: 720               # 480/720/1080

# Recognition
threshold_match: 0.62           # 0.5-0.9 (higher = stricter)
```

## 📊 Expected Performance

### Dengan NVIDIA GPU:

| Component | FPS | Latency |
|-----------|-----|---------|
| Face Detection | 15-30 | ~30ms |
| Embedding Extract | 25-60 | ~20ms |
| Full Pipeline | 12-25 | ~50ms |

### CPU Only:

| Component | FPS | Latency |
|-----------|-----|---------|
| Face Detection | 5-10 | ~100ms |
| Embedding Extract | 2-5 | ~300ms |
| Full Pipeline | 2-5 | ~400ms |

**GPU bisa 5-10x lebih cepat dari CPU!**

## 🛠️ Troubleshooting

### GPU Tidak Terdeteksi

```powershell
# Check driver
nvidia-smi

# Check CUDA
nvcc --version

# Reinstall PyTorch dengan CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory Error

Edit `config.yaml`:
```yaml
gpu_memory_fraction: 0.5  # Kurangi dari 0.8 ke 0.5
```

### Camera Tidak Terdeteksi

Edit `config.yaml`:
```yaml
camera_id: 1  # Coba index lain (0, 1, 2, ...)
```

### Performance Lambat

```yaml
# Kurangi resolusi
frame_width: 640
frame_height: 480

# Skip lebih banyak frame
grab_every_n_frames: 10
```

## 📚 Dokumentasi

| File | Deskripsi |
|------|-----------|
| `SETUP_WINDOWS_GPU.md` | Panduan setup lengkap & troubleshooting |
| `QUICK_START_ID.md` | Quick start guide (Bahasa Indonesia) |
| `COMMANDS.md` | Command cheatsheet & tips |
| `README.md` | Dokumentasi aplikasi lengkap |
| `ai_face_attendance_poc.md` | Technical documentation |

## 🎮 Keyboard Controls

Saat aplikasi running:

- `Q` - Quit
- `E` - Start enrollment
- `S` - Save snapshot
- `R` - Reset detection
- `H` - Help

## 📁 File Structure

```
project-ineffa/
├── setup_gpu_windows.ps1       # ← Setup script (JALANKAN INI!)
├── verify_setup.ps1            # ← Verifikasi setup
├── benchmark_gpu.py            # ← Test performance
├── SETUP_WINDOWS_GPU.md        # ← Panduan lengkap
├── QUICK_START_ID.md           # ← Quick start
├── COMMANDS.md                 # ← Command reference
├── main.py                     # ← Main app
├── config.yaml                 # ← Configuration (sudah optimal)
├── embedding_extractor.py      # ← GPU-enabled embedding
├── face_detection.py
├── liveness_detection.py
├── matching_engine.py
├── logging_system.py
├── ui_system.py
├── enrollment_tool.py
├── testing_tool.py
├── requirements.txt
└── venv/                       # (dibuat oleh setup script)
```

## ✨ Next Steps

1. **Setup**
   ```powershell
   .\setup_gpu_windows.ps1
   ```

2. **Verifikasi**
   ```powershell
   .\verify_setup.ps1
   ```

3. **Jalankan**
   ```powershell
   .\venv\Scripts\Activate.ps1
   python main.py
   ```

4. **Enroll Users**
   ```powershell
   python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20
   ```

5. **Enjoy!** 🎉

## 💡 Tips

- ✅ Gunakan resolusi 1280x720 untuk balance antara quality & speed
- ✅ Enroll minimal 20 images per user dengan variasi angle
- ✅ Pastikan lighting yang cukup saat enrollment & recognition
- ✅ Monitor GPU usage dengan `nvidia-smi -l 1`
- ✅ Adjust `threshold_match` di config untuk accuracy vs speed

## 🆘 Need Help?

1. Baca `SETUP_WINDOWS_GPU.md` untuk detail
2. Check `COMMANDS.md` untuk command reference
3. Jalankan `.\verify_setup.ps1` untuk diagnose
4. Check GPU dengan `nvidia-smi`

## 📊 Benchmark

Untuk test performance GPU vs CPU:

```powershell
python benchmark_gpu.py --mode compare --iterations 50
```

---

**Ready to go! Silakan jalankan `.\setup_gpu_windows.ps1` untuk memulai! 🚀**

Jika ada pertanyaan atau masalah, refer ke file dokumentasi di atas atau jalankan verification script.

# 🎯 Face Attendance PoC - Windows GPU Setup

Sistem absensi wajah offline menggunakan Face Recognition dengan akselerasi GPU NVIDIA.

## 🚀 Quick Start (3 Langkah)

### Langkah 1: Setup
```powershell
# Double-click file ini:
setup.bat

# Atau jalankan di PowerShell:
.\setup_gpu_windows.ps1
```

### Langkah 2: Verifikasi
```powershell
.\verify_setup.ps1
```

### Langkah 3: Jalankan
```powershell
# Double-click file ini:
run.bat

# Atau jalankan manual:
.\venv\Scripts\Activate.ps1
python main.py
```

**Selesai! Aplikasi siap digunakan! 🎉**

## 📚 Dokumentasi

### 🎯 Untuk Pemula

1. **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - **MULAI DARI SINI!**
   - Overview singkat
   - Quick start 3 langkah
   - Checklist lengkap

2. **[QUICK_START_ID.md](QUICK_START_ID.md)** - Panduan cepat
   - Penggunaan sehari-hari
   - Troubleshooting umum
   - Tips & tricks

3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Reference card
   - Command cepat
   - Keyboard shortcuts
   - Quick fixes

### 🔧 Untuk Troubleshooting

4. **[SETUP_WINDOWS_GPU.md](SETUP_WINDOWS_GPU.md)** - Setup detail
   - Instalasi step-by-step
   - Troubleshooting lengkap
   - Optimasi performance

5. **[COMMANDS.md](COMMANDS.md)** - Command reference
   - Semua command yang berguna
   - Configuration tips
   - One-liner commands

### 📖 Dokumentasi Lengkap

6. **[DOCS_INDEX.md](DOCS_INDEX.md)** - Index dokumentasi
   - Navigasi semua dokumen
   - Decision tree
   - File organization

7. **[README.md](README.md)** - Original documentation (English)
   - Complete system documentation
   - API reference
   - Architecture details

## 🎮 Penggunaan

### Menjalankan Aplikasi

**Option 1: Menggunakan Batch File (Termudah)**
```
Double-click: run.bat
```

**Option 2: Manual**
```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

### Keyboard Controls

| Key | Fungsi |
|-----|--------|
| `Q` | Keluar dari aplikasi |
| `E` | Mulai enrollment mode |
| `S` | Save snapshot manual |
| `R` | Reset detection |
| `H` | Tampilkan help |

### Enroll User Baru

**Option 1: Menggunakan Batch File (Termudah)**
```
Double-click: enroll.bat
Ikuti instruksi interaktif
```

**Option 2: Manual**
```powershell
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20
```

### Melihat Daftar User

```powershell
python enrollment_tool.py --mode list
```

### Testing Performance

```powershell
python benchmark_gpu.py --mode compare
```

## 📋 Prerequisites

### Hardware
- ✅ **GPU**: NVIDIA GPU dengan CUDA support (GTX 1050+)
- ✅ **RAM**: Minimal 4GB (8GB recommended)
- ✅ **Webcam**: USB atau built-in

### Software
- ✅ **Windows**: 10/11 (64-bit)
- ✅ **Python**: 3.9 - 3.11
- ✅ **NVIDIA Driver**: Versi terbaru
- ✅ **CUDA Toolkit**: 11.8 atau 12.1

## 🔍 Verifikasi Setup

```powershell
# Quick check
.\verify_setup.ps1

# Manual check GPU
nvidia-smi

# Manual check PyTorch
python -c "import torch; print('GPU Available:', torch.cuda.is_available())"
```

## ⚙️ Konfigurasi

Edit file `config.yaml` untuk mengubah settings:

```yaml
# GPU Settings
enable_gpu: true              # true = pakai GPU, false = pakai CPU
gpu_memory_fraction: 0.8      # 0.5-1.0 (penggunaan memory GPU)

# Performance
grab_every_n_frames: 5        # 3-5 untuk GPU, 7-10 untuk CPU
frame_width: 1280             # Resolusi camera
frame_height: 720

# Camera
camera_id: 0                  # Index camera (0, 1, 2, ...)

# Recognition
threshold_match: 0.62         # Threshold matching (0.5-0.9)
                              # Lebih tinggi = lebih ketat
```

## 📊 Expected Performance

### Dengan GPU (NVIDIA GTX 1060 atau lebih tinggi)
- Face Detection: 15-30 FPS
- Embedding Extraction: 25-60 FPS
- Full Pipeline: 12-25 FPS

### CPU Only (Intel i5 atau setara)
- Face Detection: 5-10 FPS
- Embedding Extraction: 2-5 FPS
- Full Pipeline: 2-5 FPS

**GPU bisa 5-10x lebih cepat!** 🚀

## 🛠️ Troubleshooting

### GPU Tidak Terdeteksi

1. Check NVIDIA driver:
```powershell
nvidia-smi
```

2. Check CUDA Toolkit:
```powershell
nvcc --version
```

3. Reinstall PyTorch dengan CUDA support:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory Error

Kurangi penggunaan GPU memory di `config.yaml`:
```yaml
gpu_memory_fraction: 0.5
```

### Camera Tidak Terdeteksi

Coba index camera yang berbeda di `config.yaml`:
```yaml
camera_id: 1  # atau 2, 3, dst.
```

Test manual:
```powershell
python -c "import cv2; cap = cv2.VideoCapture(1); print('OK' if cap.isOpened() else 'FAIL'); cap.release()"
```

### Performance Lambat

1. Kurangi resolusi camera:
```yaml
frame_width: 640
frame_height: 480
```

2. Increase frame skip:
```yaml
grab_every_n_frames: 10
```

3. Pastikan tidak ada aplikasi lain yang menggunakan GPU

**Untuk troubleshooting lengkap, lihat [SETUP_WINDOWS_GPU.md](SETUP_WINDOWS_GPU.md)**

## 📁 File Structure

```
project-ineffa/
├── 📘 DOCS (Baca ini!)
│   ├── README_ID.md              ← File ini
│   ├── SETUP_SUMMARY.md          ← START HERE
│   ├── QUICK_START_ID.md         ← Quick guide
│   ├── SETUP_WINDOWS_GPU.md      ← Detail setup
│   ├── COMMANDS.md               ← Command ref
│   ├── QUICK_REFERENCE.md        ← Quick ref card
│   └── DOCS_INDEX.md             ← Index
│
├── 🔧 SCRIPTS (Double-click untuk run!)
│   ├── setup.bat                 ← Setup
│   ├── run.bat                   ← Run app
│   ├── enroll.bat                ← Enroll user
│   ├── setup_gpu_windows.ps1     ← Setup (PS)
│   ├── verify_setup.ps1          ← Verify
│   └── benchmark_gpu.py          ← Benchmark
│
├── 🎮 APPLICATION
│   ├── main.py
│   ├── config.yaml
│   ├── embedding_extractor.py    ← GPU-enabled
│   └── ... (other Python files)
│
└── 📁 DATA (Auto-created)
    ├── venv/
    ├── gallery/
    ├── snapshots/
    ├── embeddings.json
    └── attendance.csv
```

## 🎯 Workflow

### Pertama Kali Setup
```
1. Baca SETUP_SUMMARY.md
2. Double-click setup.bat
3. Run verify_setup.ps1
4. Baca QUICK_START_ID.md
5. Double-click run.bat
6. Double-click enroll.bat (untuk enroll user)
```

### Penggunaan Sehari-hari
```
1. Double-click run.bat
2. Tekan Q untuk keluar
```

### Enroll User Baru
```
1. Double-click enroll.bat
2. Ikuti instruksi
```

## 🆘 Butuh Bantuan?

1. **Check setup**: Jalankan `.\verify_setup.ps1`
2. **Baca troubleshooting**: [SETUP_WINDOWS_GPU.md](SETUP_WINDOWS_GPU.md)
3. **Check command**: [COMMANDS.md](COMMANDS.md)
4. **Quick reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
5. **Index**: [DOCS_INDEX.md](DOCS_INDEX.md)

## 💡 Tips

- ✅ Enroll minimal 20 gambar per user untuk akurasi terbaik
- ✅ Variasi angle dan ekspresi saat enrollment
- ✅ Pastikan lighting yang cukup
- ✅ Gunakan resolusi 1280x720 untuk balance quality & speed
- ✅ Monitor GPU usage dengan `nvidia-smi -l 1`
- ✅ Adjust `threshold_match` untuk tuning accuracy

## 🔗 External Resources

- [Python Download](https://www.python.org/downloads/)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
- [NVIDIA Drivers](https://www.nvidia.com/download/index.aspx)
- [PyTorch](https://pytorch.org/get-started/locally/)

## 📄 License

Proof-of-concept untuk educational purposes. Tidak untuk production tanpa security audit.

---

## 📞 Quick Links

- 🚀 **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - Mulai dari sini!
- 📖 **[QUICK_START_ID.md](QUICK_START_ID.md)** - Quick start guide
- 🔧 **[SETUP_WINDOWS_GPU.md](SETUP_WINDOWS_GPU.md)** - Setup lengkap
- 📝 **[COMMANDS.md](COMMANDS.md)** - Command reference
- 🎴 **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick ref card
- 📚 **[DOCS_INDEX.md](DOCS_INDEX.md)** - Dokumentasi index

---

**Selamat menggunakan Face Attendance PoC! 🎉**

Jika ada pertanyaan, lihat dokumentasi di atas atau jalankan `.\verify_setup.ps1` untuk diagnostics.

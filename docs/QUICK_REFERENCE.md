# 🎴 Quick Reference Card - Face Attendance PoC

Print atau bookmark halaman ini untuk referensi cepat!

---

## ⚡ SETUP (Pertama Kali)

```powershell
# 1. Setup otomatis
.\setup_gpu_windows.ps1

# 2. Verifikasi
.\verify_setup.ps1

# ATAU double-click: setup.bat
```

---

## 🚀 DAILY USE

```powershell
# Aktifkan venv
.\venv\Scripts\Activate.ps1

# Run aplikasi
python main.py

# ATAU double-click: run.bat
```

---

## 👤 ENROLLMENT

```powershell
# Enroll user baru
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20

# List users
python enrollment_tool.py --mode list

# Remove user
python enrollment_tool.py --mode remove --user-id emp001

# ATAU double-click: enroll.bat (interactive)
```

---

## ⌨️ KEYBOARD CONTROLS

| Key | Action |
|-----|--------|
| `Q` | Quit |
| `E` | Enroll |
| `S` | Snapshot |
| `R` | Reset |
| `H` | Help |

---

## 🔍 DIAGNOSTICS

```powershell
# Check GPU
nvidia-smi

# Check PyTorch + CUDA
python -c "import torch; print('GPU:', torch.cuda.is_available())"

# Check camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL'); cap.release()"

# Verify all
.\verify_setup.ps1
```

---

## ⚙️ CONFIG (config.yaml)

```yaml
# GPU
enable_gpu: true
gpu_memory_fraction: 0.8

# Performance
grab_every_n_frames: 5    # 3-5 GPU, 7-10 CPU

# Camera
camera_id: 0              # 0, 1, 2...
frame_width: 1280
frame_height: 720

# Recognition
threshold_match: 0.62     # 0.5-0.9
```

---

## 🐛 TROUBLESHOOTING

### GPU Not Detected
```powershell
nvidia-smi                # Check driver
nvcc --version            # Check CUDA
```

### Out of Memory
```yaml
gpu_memory_fraction: 0.5  # Reduce in config.yaml
```

### Camera Not Working
```yaml
camera_id: 1              # Try different index
```

### Performance Slow
```yaml
grab_every_n_frames: 10   # Increase skip
frame_width: 640          # Reduce resolution
frame_height: 480
```

---

## 📊 BENCHMARK

```powershell
# Compare GPU vs CPU
python benchmark_gpu.py --mode compare

# Test GPU only
python benchmark_gpu.py --mode gpu --iterations 100

# Test with camera
python benchmark_gpu.py --mode pipeline --duration 30
```

---

## 📁 IMPORTANT FILES

| File | Purpose |
|------|---------|
| `config.yaml` | Configuration |
| `embeddings.json` | User data |
| `attendance.csv` | Attendance log |
| `gallery/` | User photos |
| `snapshots/` | Attendance pics |

---

## 📈 PERFORMANCE TARGETS

| Mode | FPS | Latency |
|------|-----|---------|
| GPU | 12-25 | ~50ms |
| CPU | 2-5 | ~400ms |

---

## 🔧 QUICK FIXES

```powershell
# Reinstall PyTorch + CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Clear camera
python -c "import cv2; cv2.VideoCapture(0).release()"

# Reset venv
Remove-Item -Recurse venv
python -m venv venv
```

---

## 📚 DOCUMENTATION

- **Setup:** `SETUP_SUMMARY.md`
- **Guide:** `QUICK_START_ID.md`
- **Troubleshoot:** `SETUP_WINDOWS_GPU.md`
- **Commands:** `COMMANDS.md`
- **Index:** `DOCS_INDEX.md`

---

## 🆘 HELP SEQUENCE

1. Run `.\verify_setup.ps1`
2. Check `SETUP_WINDOWS_GPU.md`
3. Search `COMMANDS.md`
4. Check GPU: `nvidia-smi`

---

## ✅ CHECKLIST

- [ ] Python 3.9-3.11
- [ ] NVIDIA Driver
- [ ] CUDA Toolkit
- [ ] venv created
- [ ] PyTorch + CUDA
- [ ] GPU detected
- [ ] Camera working
- [ ] App runs
- [ ] User enrolled

---

**💡 TIP: Bookmark this page for quick access!**

Last updated: 2025-11-13

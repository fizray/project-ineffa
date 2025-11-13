# Setup Face Attendance PoC di Windows dengan GPU Acceleration

Panduan lengkap untuk menjalankan aplikasi ini di Windows dengan akselerasi GPU NVIDIA.

## Prerequisites

### 1. Hardware Requirements
- **GPU**: NVIDIA GPU dengan CUDA support (GTX 1050 atau lebih tinggi)
- **RAM**: Minimal 4GB (8GB recommended)
- **Webcam**: USB atau built-in camera

### 2. Software Requirements
- **Windows 10/11** (64-bit)
- **Python 3.9-3.11** (64-bit) - [Download di sini](https://www.python.org/downloads/)
- **NVIDIA GPU Driver** terbaru - [Download di sini](https://www.nvidia.com/download/index.aspx)
- **CUDA Toolkit 11.8 atau 12.1** - [Download di sini](https://developer.nvidia.com/cuda-downloads)
- **cuDNN** (optional tapi recommended) - [Download di sini](https://developer.nvidia.com/cudnn)

## Langkah-langkah Setup

### Step 1: Install CUDA Toolkit

1. Download CUDA Toolkit 11.8 atau 12.1 sesuai dengan driver GPU Anda
2. Jalankan installer dan ikuti instruksi
3. Verifikasi instalasi:
```powershell
nvcc --version
```

### Step 2: Install cuDNN (Optional tapi Recommended)

1. Download cuDNN yang sesuai dengan versi CUDA Anda
2. Extract file ZIP
3. Copy file-file berikut ke folder instalasi CUDA (biasanya `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`):
   - `bin\cudnn*.dll` → `CUDA\bin\`
   - `include\cudnn*.h` → `CUDA\include\`
   - `lib\x64\cudnn*.lib` → `CUDA\lib\x64\`

### Step 3: Setup Python Virtual Environment

1. Buka PowerShell di folder project:
```powershell
cd E:\project-ineffa
```

2. Buat virtual environment:
```powershell
python -m venv venv
```

3. Aktifkan virtual environment:
```powershell
.\venv\Scripts\activate
```

4. Upgrade pip:
```powershell
python -m pip install --upgrade pip
```

### Step 4: Install PyTorch dengan CUDA Support

**Untuk CUDA 11.8:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Untuk CUDA 12.1:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Verifikasi PyTorch dengan CUDA:**
```powershell
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

Output yang benar:
```
CUDA Available: True
CUDA Version: 11.8 (atau 12.1)
GPU: NVIDIA GeForce GTX/RTX XXXX
```

### Step 5: Install Dependencies Lainnya

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

Atau gunakan requirements.txt (tapi pastikan PyTorch sudah terinstall dengan CUDA):
```powershell
pip install -r requirements.txt
```

### Step 6: Verifikasi Setup GPU

Jalankan script test berikut:
```powershell
python -c "from embedding_extractor import EmbeddingExtractor; ext = EmbeddingExtractor(model_name='vgg_face2', config={'enable_gpu': True}); print(ext.get_model_info())"
```

Output yang benar:
```
GPU enabled in config and detected: NVIDIA GeForce GTX/RTX XXXX
{'model_name': 'vgg_face2', 'device': 'cuda', 'image_size': 160, 'embedding_dim': 512, 'model_loaded': True}
```

### Step 7: Konfigurasi GPU Settings

File `config.yaml` sudah dikonfigurasi untuk GPU. Pastikan setting berikut:

```yaml
# GPU Settings
enable_gpu: true              # Enable GPU acceleration
gpu_memory_fraction: 0.8      # Gunakan 80% GPU memory
prefer_gpu: true              # Prefer GPU daripada CPU
optimize_for_gpu: true        # Optimizations untuk GPU
```

Anda bisa adjust `gpu_memory_fraction` jika GPU Anda punya memory terbatas:
- `0.5` = gunakan 50% GPU memory
- `0.8` = gunakan 80% GPU memory (recommended)
- `1.0` = gunakan semua GPU memory

### Step 8: Jalankan Aplikasi

```powershell
python main.py
```

## Troubleshooting

### GPU Tidak Terdeteksi

1. **Cek CUDA tersedia:**
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

2. **Cek versi CUDA:**
```powershell
python -c "import torch; print(torch.version.cuda)"
nvidia-smi
```

3. **Pastikan driver GPU up-to-date:**
```powershell
nvidia-smi
```

### Error "CUDA out of memory"

1. Kurangi `gpu_memory_fraction` di `config.yaml`:
```yaml
gpu_memory_fraction: 0.5
```

2. Atau kurangi resolusi camera:
```yaml
frame_width: 640
frame_height: 480
```

3. Atau proses lebih jarang:
```yaml
grab_every_n_frames: 10  # Process setiap 10 frame
```

### Error "DLL load failed" atau "cuDNN not found"

1. Install/reinstall cuDNN
2. Pastikan cuDNN files ada di CUDA directory
3. Atau install PyTorch versi CPU jika GPU terlalu ribet:
```powershell
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio
```

### Performance Masih Lambat

1. **Cek GPU Usage:**
```powershell
nvidia-smi
```

2. **Enable optimizations:**
```yaml
# Di config.yaml
optimize_for_gpu: true
fast_preview: true
processing_batch_size: 4  # Batch processing
```

3. **Tutup aplikasi lain yang pakai GPU** (game, video editor, dll)

### Camera Tidak Terdeteksi

1. Cek camera index:
```powershell
python -c "import cv2; cap = cv2.VideoCapture(0); print(f'Camera 0: {cap.isOpened()}'); cap.release()"
```

2. Coba index lain di `config.yaml`:
```yaml
camera_id: 1  # atau 2, 3, dst
```

## Performance Benchmarks

Dengan GPU acceleration, Anda seharusnya mendapat:

| Component | CPU (i5) | GPU (GTX 1060) | GPU (RTX 3060) |
|-----------|----------|----------------|----------------|
| Face Detection | ~5 FPS | ~15 FPS | ~30 FPS |
| Embedding Extract | ~2 FPS | ~25 FPS | ~60 FPS |
| Full Pipeline | ~3 FPS | ~12 FPS | ~25 FPS |

## Tips Optimasi

1. **Gunakan resolusi yang sesuai:**
   - 640x480 untuk PC biasa
   - 1280x720 untuk PC kuat
   - 1920x1080 untuk workstation

2. **Adjust frame processing:**
   ```yaml
   grab_every_n_frames: 3  # 3-5 untuk GPU, 5-10 untuk CPU
   ```

3. **Batch processing untuk enrollment:**
   ```yaml
   processing_batch_size: 8  # Lebih cepat untuk GPU
   ```

4. **Monitor GPU usage:**
   ```powershell
   nvidia-smi -l 1  # Update setiap detik
   ```

## Quick Start Commands

```powershell
# 1. Aktifkan venv
.\venv\Scripts\activate

# 2. Verifikasi GPU
python -c "import torch; print('GPU:', torch.cuda.is_available())"

# 3. Jalankan aplikasi
python main.py

# 4. Enrollment user baru
python enrollment_tool.py --mode realtime --user-id emp001 --user-name "John Doe" --num-images 20

# 5. Lihat performance
python testing_tool.py --mode report
```

## Alternative: CPU-Only Mode

Jika GPU tidak tersedia atau bermasalah, gunakan CPU mode:

```yaml
# config.yaml
enable_gpu: false
prefer_gpu: false
```

Atau install PyTorch CPU-only:
```powershell
pip install torch torchvision torchaudio
```

## Support

Jika masih ada masalah:

1. Cek versi Python: `python --version` (harus 3.9-3.11)
2. Cek CUDA: `nvcc --version`
3. Cek PyTorch: `python -c "import torch; print(torch.__version__)"`
4. Cek facenet-pytorch: `python -c "import facenet_pytorch; print('OK')"`

## Resource Links

- [PyTorch Installation](https://pytorch.org/get-started/locally/)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
- [cuDNN](https://developer.nvidia.com/cudnn)
- [NVIDIA Drivers](https://www.nvidia.com/download/index.aspx)
- [facenet-pytorch](https://github.com/timesler/facenet-pytorch)

---

**Selamat menggunakan Face Attendance PoC dengan GPU acceleration!** 🚀

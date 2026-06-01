# PROJECT INEFFA - Sistem Absensi Wajah Real-time

![Project Ineffa Demo](https://raw.githubusercontent.com/fizray/project-ineffa/rebuild/assets/demo.gif)

**PROJECT INEFFA** adalah sistem absensi otomatis berbasis pengenalan wajah yang dirancang untuk bekerja secara efisien dan real-time. Aplikasi ini mampu mendeteksi, melacak, dan mengenali wajah dari sumber video langsung (seperti webcam) untuk mencatat kehadiran secara otomatis.

---

## Daftar Isi
- [Fitur Utama](#fitur-utama)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Instalasi dan Setup](#instalasi-dan-setup)
  - [Prasyarat](#prasyarat)
  - [Instalasi (CPU)](#instalasi-cpu)
  - [Instalasi (GPU - Opsional)](#instalasi-gpu---opsional)
- [Cara Penggunaan](#cara-penggunaan)
- [Konfigurasi](#konfigurasi)
- [Dokumentasi Teknis](#dokumentasi-teknis)

---

## Fitur Utama

-   **Deteksi Wajah Cepat**: Menggunakan model YOLOv8-Face yang ringan dan akurat.
-   **Pengenalan Wajah Andal**: Ditenagai oleh model ArcFace untuk mengekstrak *face embeddings* yang unik.
-   **Pelacakan Multi-Wajah**: Menggunakan algoritma SORT untuk melacak beberapa wajah secara konsisten di seluruh frame.
-   **Pencatatan Otomatis**: Kehadiran dicatat secara otomatis ke dalam file CSV setelah wajah dikenali secara konsisten.
-   **Sangat Konfiguratif**: Hampir semua parameter (sumber video, model, ambang batas) dapat diubah melalui file `config.yaml`.
-   **Dukungan CPU & GPU**: Dapat berjalan di lingkungan CPU-only atau dipercepat dengan GPU NVIDIA.

---

## Arsitektur Sistem

Sistem ini terdiri dari beberapa modul inti yang bekerja sama:

1.  **Stream Loader**: Mengambil frame dari webcam atau file video.
2.  **Face Detector**: Menemukan lokasi wajah di setiap frame.
3.  **Embedding Extractor**: Mengubah setiap wajah menjadi vektor numerik (embedding).
4.  **Face Tracker**: Memberikan ID unik untuk setiap wajah yang bergerak.
5.  **Attendance Manager**: Mencocokkan wajah dengan database, mengenali individu, dan mencatat kehadiran.
6.  **UI System**: Menampilkan output visual (kotak, nama, status) pada layar.

---

## Instalasi dan Setup

### Prasyarat

-   Git.
-   **CPU**: Python 3.10 atau lebih tinggi.
-   **GPU NVIDIA**: Miniconda/Anaconda dan driver NVIDIA yang kompatibel.

Setup proyek memakai mode hybrid:

-   **CPU**: `.venv` lokal + `uv` untuk dependensi Python.
-   **GPU**: Conda untuk CUDA/cuDNN native, lalu `uv` untuk dependensi Python.

### Launcher All-in-One

Cara termudah adalah memakai satu launcher root:

1.  **Clone Repositori**
    ```bash
    git clone https://github.com/fizray/project-ineffa.git
    cd project-ineffa
    ```

2.  **Buka Launcher**
    Jalankan salah satu:
    ```bat
    ineffa.bat
    ```
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\ineffa.ps1
    ```

    Menu ini menangani setup, launch absensi, enrollment, benchmark, setup model, verifikasi environment, cek kamera, dan clear log.

3.  **Setup dari Menu**
    Pilih:
    -   `1. Setup auto` untuk deteksi CPU/GPU otomatis.
    -   `2. Setup CPU` untuk `.venv` + `uv`.
    -   `3. Setup GPU` untuk Conda CUDA/cuDNN + `uv`.

    Jika hanya ingin menjalankan setup langsung tanpa menu:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\setup_ineffa.ps1
    ```
    Skrip setup akan mendeteksi GPU NVIDIA. Jika GPU tersedia, setup memakai Conda + CUDA/cuDNN + `uv`. Jika tidak, setup memakai `.venv` CPU + `uv`.

    Mode juga bisa dipilih manual:
    ```powershell
    .\setup_ineffa.ps1 -Mode cpu
    .\setup_ineffa.ps1 -Mode gpu
    ```

    Opsi tambahan:
    ```powershell
    .\setup_ineffa.ps1 -Mode gpu -EnvName ineffa-gpu
    .\setup_ineffa.ps1 -Mode cpu -SkipModels
    .\setup_ineffa.ps1 -Mode gpu -RunApp
    ```

4.  **Model**
    Secara default, setup menjalankan `python scripts/setup_models.py` untuk mengunduh/mengecek model yang dibutuhkan. Di launcher, model juga bisa dicek lewat menu `7. Setup/check models`.

### Instalasi (GPU - Opsional)

Untuk performa yang jauh lebih baik, gunakan mode GPU:

```powershell
.\setup_ineffa.ps1 -Mode gpu
```

Mode ini membuat environment Conda `ineffa-gpu`, memasang `cudatoolkit=11.8`, `cudnn=8.9.2`, dan `zlib-wapi`, lalu memasang dependency Python dari `requirements-gpu.txt` memakai `uv`. `onnxruntime-gpu==1.16.3` tetap dipin untuk kompatibilitas CUDA 11.8.

---

## Cara Penggunaan

Jalankan `ineffa.bat`, lalu pilih menu:

-   `4. Attendance` untuk menjalankan aplikasi absensi.
-   `5. Enroll user` untuk mendaftarkan wajah baru.
-   `6. Benchmark` untuk menjalankan benchmark.
-   `8. Verify environment` untuk cek dependency dan ONNX provider.
-   `9. Check cameras` untuk cek kamera yang terdeteksi.

Launcher menjalankan Python environment secara langsung. Untuk GPU, launcher memakai `python.exe` dari Conda env `ineffa-gpu`, bukan `conda run`, sehingga menu interaktif tidak terkena `EOFError`.

---

## Konfigurasi

Semua pengaturan utama dapat ditemukan dan diubah di `config.yaml`. Anda dapat menyesuaikan:
-   Sumber input video (`source`).
-   Model yang digunakan (`model_path`).
-   Ambang batas kepercayaan dan pengenalan (`confidence_threshold`, `recognition_threshold`).
-   Dan banyak lagi.

Untuk detail lengkap tentang setiap parameter, lihat dokumentasi konfigurasi.

---

## Dokumentasi Teknis

Untuk pemahaman yang lebih mendalam tentang cara kerja setiap komponen, silakan merujuk ke dokumentasi teknis di direktori `docs/`:

-   [`docs/configuration.md`](./docs/configuration.md): Penjelasan lengkap file `config.yaml`.
-   [`docs/core_modules.md`](./docs/core_modules.md): Detail tentang modul-modul di direktori `core/`.
-   [`docs/scripts_and_tools.md`](./docs/scripts_and_tools.md): Penjelasan skrip bantu seperti `enrollment_tool.py`.
-   [`docs/setup_linux_cpu.md`](./docs/setup_linux_cpu.md): Panduan instalasi untuk Linux (Debian/Ubuntu) dengan CPU.

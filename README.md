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
  - [1. Mendaftarkan Wajah Baru](#1-mendaftarkan-wajah-baru)
  - [2. Menjalankan Aplikasi Absensi](#2-menjalankan-aplikasi-absensi)
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

-   Python 3.8 atau lebih tinggi.
-   Conda (dianjurkan untuk manajemen environment).
-   Git.
-   **Untuk GPU**: Driver NVIDIA dan CUDA Toolkit yang kompatibel.

### Instalasi (CPU)

Cara termudah untuk menginstal adalah dengan menggunakan skrip yang disediakan.

1.  **Clone Repositori**
    ```bash
    git clone https://github.com/fizray/project-ineffa.git
    cd project-ineffa
    ```

2.  **Jalankan Skrip Setup Conda**
    Buka Command Prompt atau PowerShell, lalu jalankan:
    ```bash
    setup_conda.bat
    ```
    Skrip ini akan secara otomatis:
    -   Membuat environment Conda baru bernama `ineffa-env`.
    -   Mengaktifkan environment tersebut.
    -   Menginstal semua pustaka Python yang diperlukan dari `requirements.txt`.

3.  **Unduh Model**
    Pastikan Anda memiliki model yang diperlukan di dalam direktori `models/`:
    -   `yolov8n-face.pt` (untuk deteksi wajah)
    -   `mobile_net_v2_arcface.onnx` (untuk ekstraksi embedding)
    *Catatan: Tautan untuk mengunduh model dapat ditemukan di dokumentasi atau repositori aslinya.*

### Instalasi (GPU - Opsional)

Untuk performa yang jauh lebih baik, Anda dapat menggunakan GPU NVIDIA.

1.  **Pastikan Driver dan CUDA Terinstal**: Ikuti panduan resmi NVIDIA untuk menginstal driver kartu grafis Anda dan CUDA Toolkit yang sesuai.
2.  **Jalankan Skrip Setup GPU**: Gunakan skrip PowerShell yang dirancang untuk ini. Buka PowerShell sebagai Administrator, lalu jalankan:
    ```powershell
    # Izinkan eksekusi skrip (jika belum)
    Set-ExecutionPolicy Unrestricted -Force

    # Jalankan skrip setup GPU
    .\scripts\setup_conda_gpu.ps1
    ```
    Skrip ini akan menginstal PyTorch versi GPU dan dependensi CUDA lainnya di dalam environment Conda.

---

## Cara Penggunaan

### 1. Mendaftarkan Wajah Baru

Sebelum sistem dapat mengenali siapa pun, Anda harus mendaftarkan wajah mereka terlebih dahulu.

-   Aktifkan environment Conda Anda:
    ```bash
    conda activate ineffa-env
    ```
-   Jalankan alat pendaftaran:
    ```bash
    python enrollment_tool.py
    ```
-   Masukkan nama orang yang akan didaftarkan, lalu posisikan wajah di depan kamera. Sistem akan secara otomatis mengambil beberapa sampel dan menyimpannya.

### 2. Menjalankan Aplikasi Absensi

Setelah wajah terdaftar, Anda siap menjalankan aplikasi utama.

-   Pastikan environment Conda aktif.
-   Jalankan aplikasi melalui skrip `launch.py`:
    ```bash
    python launch.py
    ```
-   Aplikasi akan membuka jendela yang menampilkan feed kamera. Ketika wajah yang terdaftar terdeteksi, namanya akan muncul, dan absensi akan dicatat.

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

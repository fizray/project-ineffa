# Dokumentasi Skrip dan Alat Bantu

Repositori ini menyertakan beberapa skrip dan alat untuk mempermudah instalasi, pendaftaran, dan eksekusi aplikasi.

---

### 1. `enrollment_tool.py`

**Tujuan:** Mendaftarkan wajah baru ke dalam sistem dengan mengambil beberapa gambar, mengekstrak embedding, dan menyimpannya.

**Cara Kerja:**
1.  Menerima ID dan Nama pengguna melalui argumen command line.
2.  Membuka webcam dan mendeteksi wajah.
3.  Memvalidasi kualitas wajah (ukuran, jumlah wajah).
4.  Pengguna menekan tombol 'c' untuk mengambil sampel (capture).
5.  Setelah jumlah sampel terpenuhi (default: 5), embedding disimpan ke `data/embeddings.json`.

**Cara Menggunakan:**
```bash
python enrollment_tool.py --id "1001" --name "Budi Santoso" --samples 5
```
-   `--id`: ID unik untuk pengguna (wajib).
-   `--name`: Nama lengkap pengguna (wajib).
-   `--samples`: Jumlah sampel foto yang diambil (opsional, default 5).

---

### 2. `main.py`

**Tujuan:** Skrip utama yang mengintegrasikan semua modul `core` untuk menjalankan aplikasi absensi wajah secara real-time.

**Alur Eksekusi:**
1.  **Inisialisasi:**
    -   Memuat konfigurasi dari `config.yaml`.
    -   Menginisialisasi `RTSPStreamLoader`, `FaceDetector`, `LivenessDetector`, `RecognitionEngine`, `CentroidTracker`, `AttendanceManager`, dan `UISystem`.
    -   Memuat database embedding wajah.
2.  **Loop Utama:**
    -   Membaca frame dari stream.
    -   **Pra-pemrosesan:** Menerapkan CLAHE (jika diaktifkan) untuk perbaikan kontras.
    -   **Deteksi:** Mendeteksi wajah menggunakan InsightFace.
    -   **Tracking:** Memperbarui posisi wajah dengan Centroid Tracker.
    -   **Logika Pengenalan:**
        -   Cek ukuran wajah minimum.
        -   **Liveness Check:** Memastikan wajah asli (bukan spoof) menggunakan MiniFASNetV2.
        -   **Identifikasi:** Mencocokkan embedding dengan database.
        -   **Logging:** Mencatat absensi jika valid dan lolos cooldown.
    -   **Tampilan:** Menggambar overlay status dan dashboard pada frame.
3.  **Pembersihan:**
    -   Menekan 'q' untuk keluar dan melepaskan resource.

---

### 3. `launch.py`

**Tujuan:** Skrip sederhana untuk meluncurkan `main.py`.

**Cara Menggunakan:**
```bash
python launch.py
```

---

### 4. Skrip Setup (`setup_conda.bat`, `run_gpu.bat`, dll.)

-   **`setup_conda.bat`**: Skrip batch untuk Windows yang membuat lingkungan Conda baru, menginstal Python, dan dependensi dari `requirements.txt`.

-   **`run_gpu.bat`**: Skrip untuk menjalankan aplikasi dengan konfigurasi GPU yang optimal.

-   **`scripts/setup_conda_gpu.ps1`**: Skrip PowerShell untuk setup lingkungan Conda dengan dukungan GPU (CUDA/cuDNN).

-   **`scripts/setup_gpu_windows.ps1`**: Skrip instalasi driver NVIDIA dan CUDA Toolkit di Windows.

-   **`scripts/verify_setup.ps1`**: Memverifikasi instalasi PyTorch dan ketersediaan CUDA.

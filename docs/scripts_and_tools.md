# Dokumentasi Skrip dan Alat Bantu

Repositori ini menyertakan beberapa skrip dan alat untuk mempermudah instalasi, pendaftaran, dan eksekusi aplikasi.

---

### 1. `enrollment_tool.py`

**Tujuan:** Mendaftarkan wajah baru ke dalam sistem dengan mengambil beberapa gambar, mengekstrak embedding, dan menyimpannya.

**Cara Kerja:**
1.  Meminta pengguna memasukkan nama.
2.  Membuka webcam dan mulai mendeteksi wajah.
3.  Ketika wajah terdeteksi dengan jelas, alat ini akan mengambil beberapa sampel gambar (misalnya, 20 sampel).
4.  Untuk setiap sampel, embedding wajah diekstraksi.
5.  Rata-rata dari semua embedding yang terkumpul dihitung untuk menghasilkan satu embedding representatif untuk orang tersebut.
6.  Nama dan embedding representatif ini kemudian disimpan ke dalam file `data/embeddings.json`.

**Cara Menggunakan:**
```bash
python enrollment_tool.py
```
Ikuti instruksi di terminal dan pastikan wajah Anda terlihat jelas di depan kamera.

---

### 2. `main.py`

**Tujuan:** Skrip utama yang mengintegrasikan semua modul `core` untuk menjalankan aplikasi absensi wajah secara real-time.

**Alur Eksekusi:**
1.  **Inisialisasi:**
    -   Memuat konfigurasi dari `config.yaml`.
    -   Menginisialisasi semua objek dari modul `core`: `StreamLoader`, `FaceDetector`, `EmbeddingExtractor`, `FaceTracker`, `AttendanceManager`, dan `UISystem`.
2.  **Loop Utama:**
    -   Membaca frame dari `StreamLoader`.
    -   Mendeteksi wajah dalam frame menggunakan `FaceDetector`.
    -   Memperbarui pelacak dengan deteksi baru menggunakan `FaceTracker`.
    -   Mengenali wajah yang dilacak dan mencatat absensi menggunakan `AttendanceManager`.
    -   Menampilkan hasil (kotak pembatas, nama, FPS) pada frame menggunakan `UISystem`.
    -   Menampilkan frame yang sudah diproses di jendela OpenCV.
3.  **Pembersihan:**
    -   Ketika pengguna menekan tombol 'q', loop berhenti, dan semua sumber daya (seperti kamera) dilepaskan.

---

### 3. `launch.py`

**Tujuan:** Skrip sederhana untuk meluncurkan `main.py`. Ini bisa digunakan di masa depan untuk menambahkan logika tambahan sebelum aplikasi utama berjalan (misalnya, memeriksa pembaruan, mengatur variabel lingkungan).

**Cara Menggunakan:**
```bash
python launch.py
```

---

### 4. Skrip Setup (`setup_conda.bat`, `run_gpu.bat`, dll.)

-   **`setup_conda.bat`**: Skrip batch untuk Windows yang membuat lingkungan Conda baru bernama `ineffa-env`, menginstal Python, dan kemudian menginstal semua dependensi yang tercantum dalam `requirements.txt` menggunakan `pip`.

-   **`run_gpu.bat`**: Contoh skrip untuk menjalankan aplikasi dengan akselerasi GPU (jika dependensi GPU telah diinstal). Biasanya, ini akan mengatur variabel lingkungan atau menggunakan versi pustaka yang dikompilasi khusus untuk GPU.

-   **`scripts/setup_conda_gpu.ps1`**: Skrip PowerShell yang lebih canggih untuk mengatur lingkungan Conda dengan dukungan GPU. Ini akan menginstal `cudatoolkit` dan `cudnn` dari channel `nvidia` bersama dengan `pytorch` versi GPU.

-   **`scripts/setup_gpu_windows.ps1`**: Skrip yang mungkin berisi langkah-langkah untuk menginstal driver NVIDIA dan CUDA Toolkit di tingkat sistem operasi Windows.

-   **`scripts/verify_setup.ps1`**: Skrip untuk memverifikasi bahwa semua dependensi (terutama yang terkait GPU seperti PyTorch dan CUDA) telah terinstal dengan benar dan dapat diakses oleh Python.

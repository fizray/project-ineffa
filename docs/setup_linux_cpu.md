# Panduan Setup Project Ineffa di Linux (Debian/Ubuntu) dengan CPU

Dokumen ini menjelaskan langkah-langkah untuk menyiapkan dan menjalankan **Project Ineffa** pada sistem operasi berbasis Debian atau Ubuntu menggunakan **Miniconda** dan **CPU**.

Panduan ini cocok untuk:
- Server tanpa GPU.
- Laptop atau PC Linux standar.
- Perangkat edge seperti Raspberry Pi (dengan OS 64-bit).

---

## 1. Persiapan Sistem

Sebelum memulai, pastikan sistem Anda sudah diperbarui dan memiliki dependensi dasar.

Buka terminal dan jalankan perintah berikut:

```bash
# Update daftar paket
sudo apt update && sudo apt upgrade -y

# Instal dependensi dasar yang sering dibutuhkan oleh OpenCV dan Python
# Catatan: Pada Ubuntu versi baru (22.04+), libgl1-mesa-glx digantikan oleh libgl1
sudo apt install -y build-essential libgl1 libglib2.0-0 git wget
```

---

## 2. Instalasi Miniconda

Jika Anda belum memiliki Conda, instal Miniconda terlebih dahulu. Miniconda adalah versi minimal dari Anaconda yang ringan.

1.  **Unduh Installer Miniconda**:
    ```bash
    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    ```

2.  **Jalankan Installer**:
    ```bash
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    ```

3.  **Inisialisasi Conda**:
    ```bash
    ~/miniconda3/bin/conda init bash
    ```

4.  **Muat Ulang Shell**:
    Tutup terminal dan buka kembali, atau jalankan:
    ```bash
    source ~/.bashrc
    ```

---

## 3. Setup Environment Project Ineffa

Sekarang kita akan membuat environment khusus untuk proyek ini agar tidak mengganggu sistem Python utama.

1.  **Clone Repository** (jika belum):
    ```bash
    git clone https://github.com/hyacinthlabs/project-ineffa.git
    cd project-ineffa
    ```

2.  **Buat Environment Conda**:
    Kita akan menggunakan Python 3.10 yang stabil.
    ```bash
    conda create -n ineffa-cpu python=3.10 -y
    ```

3.  **Aktifkan Environment**:
    ```bash
    conda activate ineffa-cpu
    ```

4.  **Instal Dependensi**:
    Karena kita menggunakan CPU, kita perlu menyesuaikan beberapa paket dari `requirements.txt` (terutama `onnxruntime-gpu` menjadi `onnxruntime`).

    Jalankan perintah berikut untuk menginstal paket-paket utama secara manual agar lebih aman:

    ```bash
    # Instal paket dasar
    pip install numpy opencv-python pyyaml tqdm requests pillow scikit-learn filterpy lap

    # Instal InsightFace (untuk pengenalan wajah)
    pip install insightface

    # Instal ONNX Runtime versi CPU
    pip install onnxruntime
    ```

    *Catatan: Jika Anda melihat error terkait `onnxruntime-gpu` saat mencoba menginstal dari requirements.txt, abaikan saja dan pastikan `onnxruntime` (versi CPU) sudah terinstal.*

---

## 4. Verifikasi Instalasi

Untuk memastikan semuanya berjalan lancar, Anda bisa menjalankan skrip verifikasi sederhana atau langsung mencoba aplikasi.

1.  **Cek Import Python**:
    ```bash
    python -c "import cv2; import onnxruntime; import insightface; print('Semua modul berhasil dimuat!')"
    ```
    Jika tidak ada error, berarti instalasi berhasil.

2.  **Cek Model**:
    Jalankan skrip berikut untuk mengunduh model yang diperlukan (InsightFace & Liveness) secara otomatis:
    ```bash
    python scripts/setup_models.py
    ```
    Skrip ini akan:
    - Mengunduh model `buffalo_l` ke `~/.insightface/models/`.
    - Mengunduh model liveness `2.7_80x80_MiniFASNetV2.onnx` ke folder `models/` di proyek.

---

## 5. Menjalankan Aplikasi

### Mode Benchmark (Uji Performa)
Untuk menguji seberapa cepat CPU Anda menangani proses pengenalan wajah:

```bash
python bench.py
```
Pilih opsi **1. Run Benchmark** di menu.

### Mode Absensi (Utama)
Untuk menjalankan sistem absensi utama:

```bash
python launch.py
```
Atau langsung ke skrip utama:
```bash
python main.py
```

---

## Tips Optimasi CPU

Jika aplikasi terasa lambat di CPU, Anda bisa melakukan beberapa penyesuaian di `config.yaml`:

1.  **Gunakan Model Deteksi yang Lebih Ringan**:
    Ubah `detection.model_name` menjadi `buffalo_s` (lebih cepat tapi sedikit kurang akurat untuk wajah jauh).
    ```yaml
    detection:
      model_name: "buffalo_s"
    ```

2.  **Kurangi Resolusi Input**:
    Ubah `input.width` dan `input.height` ke resolusi yang lebih rendah, misalnya 640x480 atau 1280x720.
    ```yaml
    input:
      width: 640
      height: 480
    ```

3.  **Kurangi Ukuran Input Deteksi**:
    Ubah `detection.input_size` ke nilai yang lebih kecil (misal 320 atau 640).
    ```yaml
    detection:
      input_size: 320
    ```

4.  **Matikan Fitur Berat**:
    Jika tidak diperlukan, matikan `liveness` check.
    ```yaml
    liveness:
      enabled: false
    ```

---

## Troubleshooting Umum

-   **Error `libGL.so.1: cannot open shared object file`**:
    Ini berarti library OpenGL belum terinstal. Jalankan:
    ```bash
    sudo apt install libgl1
    ```

-   **Error `libgthread-2.0.so.0`**:
    Jalankan:
    ```bash
    sudo apt install libglib2.0-0
    ```

-   **Kamera tidak terdeteksi**:
    Pastikan user Anda memiliki akses ke perangkat video:
    ```bash
    sudo usermod -aG video $USER
    ```
    Lalu logout dan login kembali.

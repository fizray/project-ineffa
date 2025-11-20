# Dokumentasi Modul Inti (`core/`)

Direktori `core/` berisi modul-modul Python yang menjadi komponen utama dari sistem absensi wajah. Setiap file memiliki tanggung jawab spesifik.

---

### 1. `stream_loader.py`

**Tujuan:** Mengelola pengambilan frame dari berbagai sumber video seperti webcam atau file video.

**Class: `StreamLoader`**

-   **`__init__(self, source, resolution, fps)`**:
    -   Menginisialisasi objek `VideoCapture` dari OpenCV.
    -   Mengatur resolusi dan FPS yang diinginkan.
    -   Memulai thread terpisah untuk membaca frame secara terus-menerus, yang mencegah pembekuan (blocking) pada thread utama.

-   **`read(self)`**:
    -   Mengembalikan frame terbaru yang telah dibaca oleh thread latar belakang.

-   **`stop(self)`**:
    -   Menghentikan thread dan melepaskan sumber video.

---

### 2. `face_detection.py`

**Tujuan:** Mendeteksi lokasi wajah dalam sebuah frame menggunakan model YOLOv8.

**Class: `FaceDetector`**

-   **`__init__(self, model_path, confidence_threshold)`**:
    -   Memuat model deteksi wajah YOLO dari path yang diberikan.
    -   Menyimpan ambang batas kepercayaan (confidence threshold).

-   **`detect(self, frame)`**:
    -   Menerima sebuah frame gambar.
    -   Menjalankan inferensi model pada frame.
    -   Menyaring hasil deteksi berdasarkan ambang batas kepercayaan.
    -   Mengembalikan daftar kotak pembatas (bounding boxes) dari wajah yang terdeteksi.

---

### 3. `embedding_extractor.py`

**Tujuan:** Mengekstrak fitur wajah (embedding) dari gambar wajah yang telah dipotong (cropped).

**Class: `EmbeddingExtractor`**

-   **`__init__(self, model_path, input_size)`**:
    -   Memuat model inferensi ONNX (misalnya, ArcFace) untuk ekstraksi embedding.
    -   Menyimpan ukuran input yang diharapkan oleh model.

-   **`extract(self, frame, face_bbox)`**:
    -   Menerima frame asli dan kotak pembatas wajah.
    -   Memotong (crop) wajah dari frame.
    -   Melakukan pra-pemrosesan pada gambar wajah (mengubah ukuran, normalisasi).
    -   Menjalankan inferensi untuk mendapatkan vektor embedding.
    -   Mengembalikan embedding yang telah dinormalisasi.

---

### 4. `tracker.py`

**Tujuan:** Melacak wajah yang terdeteksi di beberapa frame untuk memberikan ID yang konsisten.

**Class: `FaceTracker`**

-   **`__init__(self, max_age, min_hits, iou_threshold)`**:
    -   Menginisialisasi objek `Sort` dari library `sort-py` dengan parameter yang diberikan.

-   **`update(self, detections)`**:
    -   Menerima daftar deteksi wajah (bounding boxes) dari `FaceDetector`.
    -   Memperbarui status pelacak.
    -   Mengembalikan array yang berisi `[x1, y1, x2, y2, track_id]` untuk setiap wajah yang dilacak.

---

### 5. `attendance_manager.py`

**Tujuan:** Komponen sentral yang mengelola logika pengenalan wajah, pencocokan, dan pencatatan absensi.

**Class: `AttendanceManager`**

-   **`__init__(self, embeddings_path, ...)`**:
    -   Memuat embedding wajah yang telah terdaftar dari file JSON.
    -   Menginisialisasi status pelacakan untuk setiap ID (misalnya, jumlah frame terdeteksi, status pengenalan).

-   **`recognize_and_log(self, frame, tracked_faces)`**:
    -   Untuk setiap wajah yang dilacak:
        1.  Mengekstrak embedding wajah saat ini.
        2.  Membandingkan embedding tersebut dengan semua embedding yang terdaftar menggunakan kemiripan kosinus (cosine similarity).
        3.  Jika kemiripan melebihi `recognition_threshold` untuk nama tertentu secara konsisten (selama `consecutive_frames_for_recognition`), wajah dianggap dikenali.
        4.  Jika wajah dikenali dan belum diabsen hari itu, catat absensi ke file CSV.
        5.  Jika kemiripan tertinggi di bawah `unknown_threshold`, tandai sebagai "Tidak Dikenal".
    -   Mengembalikan status pengenalan untuk setiap wajah yang dilacak.

---

### 6. `ui_system.py`

**Tujuan:** Menangani semua rendering visual, seperti menggambar kotak pembatas, nama, dan informasi lainnya pada frame.

**Class: `UISystem`**

-   **`__init__(self, font_path, font_size, ...)`**:
    -   Menginisialisasi pengaturan font dan tema warna.

-   **`display(self, frame, tracked_faces, recognition_results, fps)`**:
    -   Menerima frame asli, hasil pelacakan, dan hasil pengenalan.
    -   Menggambar kotak pembatas di sekitar setiap wajah. Warna kotak disesuaikan berdasarkan status (misalnya, hijau untuk "dikenali", biru untuk "tidak dikenal", oranye untuk "sedang dilacak").
    -   Menuliskan nama atau status di atas kotak pembatas.
    -   Jika `show_fps` diaktifkan, menampilkan FPS di sudut layar.
    -   Mengembalikan frame yang telah dimodifikasi dan siap untuk ditampilkan.

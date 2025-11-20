# Dokumentasi Modul Inti (`core/`)

Direktori `core/` berisi modul-modul Python yang menjadi komponen utama dari sistem absensi wajah. Setiap file memiliki tanggung jawab spesifik.

---

### 1. `stream_loader.py`

**Tujuan:** Mengelola pengambilan frame dari berbagai sumber video seperti webcam, file video, atau stream RTSP.

**Class: `RTSPStreamLoader`**

-   **`__init__(self, source, width, height, reconnect_delay)`**:
    -   Menginisialisasi koneksi ke sumber video.
    -   Mendukung webcam (index integer) dan RTSP/File (string).
    -   Memulai thread terpisah untuk membaca frame secara terus-menerus (non-blocking).

-   **`read(self)`**:
    -   Mengembalikan frame terbaru dari antrian (queue).
    -   Menggunakan mekanisme bufferless (hanya menyimpan frame terakhir) untuk latensi rendah.

-   **`stop(self)`**:
    -   Menghentikan thread dan melepaskan sumber video.

---

### 2. `face_detection.py`

**Tujuan:** Mendeteksi lokasi wajah dalam sebuah frame menggunakan model dari InsightFace.

**Class: `FaceDetector`**

-   **`__init__(self, app, conf_threshold, nms_threshold)`**:
    -   Menerima objek aplikasi InsightFace yang sudah diinisialisasi.
    -   Menyimpan ambang batas kepercayaan dan NMS.

-   **`detect(self, frame)`**:
    -   Menjalankan deteksi wajah pada frame.
    -   Mengembalikan daftar objek `Face` yang berisi bounding box, keypoints (landmarks), dan skor deteksi.

---

### 3. `embedding_extractor.py`

**Tujuan:** Mengekstrak fitur wajah (embedding) dan menghitung kemiripan.

**Class: `RecognitionEngine`**

-   **`__init__(self, app)`**:
    -   Menggunakan model pengenalan dari aplikasi InsightFace.

-   **`get_embedding(self, frame, face_obj)`**:
    -   Mengekstrak vektor embedding (512-dimensi) dari wajah.
    -   Melakukan alignment wajah otomatis berdasarkan keypoints sebelum ekstraksi.

-   **`compute_similarity(self, embed1, embed2)`**:
    -   Menghitung Cosine Similarity antara dua vektor embedding.

---

### 4. `tracker.py`

**Tujuan:** Melacak wajah yang terdeteksi di beberapa frame untuk memberikan ID yang konsisten.

**Class: `CentroidTracker`**

-   **`__init__(self, max_disappeared, max_distance)`**:
    -   Menginisialisasi pelacak berbasis centroid.

-   **`update(self, rects)`**:
    -   Menerima daftar bounding box.
    -   Menghitung centroid (titik tengah) dari setiap box.
    -   Mencocokkan centroid baru dengan centroid objek yang sudah ada berdasarkan jarak Euclidean terdekat.
    -   Mengembalikan dictionary `{object_id: centroid}`.

---

### 5. `attendance_manager.py`

**Tujuan:** Mengelola pencatatan absensi dan penyimpanan data log.

**Class: `AttendanceManager`**

-   **`__init__(self, config)`**:
    -   Memuat konfigurasi path log dan cooldown.

-   **`log_attendance(self, name, frame, bbox)`**:
    -   Mengecek apakah pengguna sedang dalam masa "cooldown" (baru saja absen).
    -   Jika valid, mencatat waktu dan nama ke file CSV.
    -   Menyimpan foto wajah (snapshot) ke folder `data/captures/`.
    -   Memperbarui log aktivitas terbaru untuk UI.

-   **`get_recent_logs(self)`**:
    -   Mengembalikan daftar log terbaru untuk ditampilkan di sidebar UI.

---

### 6. `ui_system.py`

**Tujuan:** Menangani tampilan visual antarmuka pengguna.

**Class: `UISystem`**

-   **`__init__(self, config)`**:
    -   Menginisialisasi font dan palet warna.

-   **`draw_dashboard(self, frame, tracked_faces, faces_map, recent_logs, is_connected)`**:
    -   Menggambar kotak pembatas wajah dengan warna sesuai status (Dikenal/Hijau, Tidak Dikenal/Kuning, Spoof/Merah).
    -   Menampilkan header status sistem (FPS, Koneksi).
    -   Menampilkan sidebar daftar absensi terbaru.

---

### 7. `liveness_detector.py`

**Tujuan:** Memastikan wajah yang terdeteksi adalah wajah asli (bukan foto atau layar).

**Class: `LivenessDetector`**

-   **`__init__(self, config)`**:
    -   Memuat model anti-spoofing (MiniFASNetV2) dalam format ONNX.

-   **`check_liveness(self, frame, bbox)`**:
    -   Memotong area wajah dan memperluasnya (scale 2.7x) untuk konteks.
    -   Menjalankan inferensi model liveness.
    -   Mengembalikan `True` jika wajah asli, dan skor keasliannya.

# Dokumentasi Konfigurasi (config.yaml)

File `config.yaml` adalah pusat kendali untuk semua pengaturan penting dalam aplikasi absensi wajah. Dengan mengubah nilai-nilai di file ini, Anda dapat menyesuaikan perilaku aplikasi tanpa harus mengubah kode sumber.

## Struktur Konfigurasi

```yaml
# Pengaturan Umum
project_name: "PROJECT INEFFA"
version: "1.0"

# Pengaturan Sumber Video
stream_loader:
  source: 0  # 0 untuk webcam, atau path ke file video
  resolution: [1280, 720]
  fps: 30

# Pengaturan Deteksi Wajah
face_detection:
  model_path: "models/yolov8n-face.pt"
  confidence_threshold: 0.5

# Pengaturan Ekstraksi Embedding
embedding_extractor:
  model_path: "models/mobile_net_v2_arcface.onnx"
  input_size: [112, 112]

# Pengaturan Pelacakan (Tracker)
tracker:
  max_age: 30
  min_hits: 3
  iou_threshold: 0.3

# Pengaturan Manajer Absensi
attendance_manager:
  embeddings_path: "data/embeddings.json"
  attendance_log_path: "data/attendance.csv"
  recognition_threshold: 0.65 # Ambang batas kemiripan untuk mengenali wajah
  unknown_threshold: 0.55   # Ambang batas untuk menandai sebagai "tidak dikenal"
  consecutive_frames_for_recognition: 5 # Jumlah frame berturut-turut untuk konfirmasi

# Pengaturan UI
ui_system:
  font_path: "C:/Windows/Fonts/Arial.ttf"
  font_size: 16
  show_fps: true
  theme:
    background: [25, 25, 25]
    text: [255, 255, 255]
    bbox_known: [0, 255, 0]
    bbox_unknown: [0, 0, 255]
    bbox_tracking: [255, 165, 0]
```

## Penjelasan Setiap Bagian

### `project_name` & `version`
-   **`project_name`**: Nama proyek yang akan ditampilkan di jendela aplikasi.
-   **`version`**: Versi aplikasi.

### `stream_loader`
Bagian ini mengontrol sumber input video.
-   **`source`**: Menentukan sumber video.
    -   Gunakan `0` untuk webcam utama, `1` untuk webcam kedua, dan seterusnya.
    -   Anda juga bisa memberikan path ke file video (misalnya, `"path/to/your/video.mp4"`).
-   **`resolution`**: Resolusi yang diinginkan untuk video (lebar, tinggi).
-   **`fps`**: Frame per second (FPS) yang diinginkan dari sumber video.

### `face_detection`
Pengaturan untuk model deteksi wajah (YOLOv8).
-   **`model_path`**: Path ke file model deteksi wajah (`.pt`).
-   **`confidence_threshold`**: Ambang batas kepercayaan. Hanya deteksi dengan skor di atas nilai ini yang akan diproses. Nilai antara 0 dan 1.

### `embedding_extractor`
Pengaturan untuk model yang mengubah wajah menjadi representasi numerik (embedding).
-   **`model_path`**: Path ke file model ArcFace (`.onnx`).
-   **`input_size`**: Ukuran gambar wajah yang diharapkan oleh model (lebar, tinggi).

### `tracker`
Mengonfigurasi algoritma pelacakan (SORT) untuk menjaga ID yang konsisten pada wajah yang terdeteksi.
-   **`max_age`**: Jumlah frame maksimum di mana sebuah track akan dipertahankan tanpa deteksi baru.
-   **`min_hits`**: Jumlah deteksi minimum yang diperlukan untuk memulai sebuah track.
-   **`iou_threshold`**: Ambang batas Intersection over Union (IoU) untuk mengasosiasikan deteksi dengan track yang ada.

### `attendance_manager`
Mengelola logika inti untuk pengenalan wajah dan pencatatan absensi.
-   **`embeddings_path`**: Path ke file JSON yang menyimpan embedding wajah dari orang-orang yang terdaftar.
-   **`attendance_log_path`**: Path ke file CSV tempat catatan absensi akan disimpan.
-   **`recognition_threshold`**: Ambang batas kemiripan kosinus. Jika kemiripan antara wajah yang terdeteksi dan embedding yang tersimpan di atas nilai ini, wajah tersebut dianggap "dikenali".
-   **`unknown_threshold`**: Jika kemiripan tertinggi di bawah ambang batas ini, wajah akan ditandai sebagai "Tidak Dikenal".
-   **`consecutive_frames_for_recognition`**: Wajah harus dikenali secara konsisten selama jumlah frame ini sebelum absensi dicatat. Ini mencegah kesalahan pengenalan sesaat.

### `ui_system`
Mengontrol aspek visual dari antarmuka pengguna.
-   **`font_path`**: Path ke file font (`.ttf`) yang akan digunakan untuk teks pada layar.
-   **`font_size`**: Ukuran font.
-   **`show_fps`**: Jika `true`, akan menampilkan FPS saat ini di layar.
-   **`theme`**: Pengaturan warna untuk berbagai elemen UI seperti latar belakang, teks, dan kotak pembatas (bounding box) untuk status yang berbeda (dikenali, tidak dikenali, sedang dilacak).

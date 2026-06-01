# Dokumentasi Konfigurasi (config.yaml)

File `config.yaml` adalah pusat kendali untuk semua pengaturan penting dalam aplikasi absensi wajah. Dengan mengubah nilai-nilai di file ini, Anda dapat menyesuaikan perilaku aplikasi tanpa harus mengubah kode sumber.

## Struktur Konfigurasi

```yaml
system:
  mode: "attendance" # Options: "attendance", "enrollment"
  gpu_enabled: true
  debug_mode: false
  log_level: "INFO"

input:
  # Konfigurasi Sumber
  # Untuk Webcam: gunakan integer (misal: 0, 1)
  # Untuk RTSP: gunakan string (misal: "rtsp://admin:pass@192.168.1.10:554/stream")
  source: 0
  
  width: 1280
  height: 720
  fps_limit: 60
  reconnect_delay: 5 # Detik menunggu sebelum mencoba koneksi ulang RTSP
  
  # Pra-pemrosesan Gambar untuk CCTV/Pencahayaan Buruk
  preprocessing:
    enable_clahe: true # Meningkatkan kontras pada bayangan/silau
    clahe_clip_limit: 2.0
    clahe_tile_grid_size: 8

detection:
  # Options: "yolov8n-face", "buffalo_l" (RetinaFace), "buffalo_s"
  model_name: "buffalo_l" 
  confidence_threshold: 0.4 # Diturunkan untuk CCTV agar menangkap wajah yang sulit
  nms_threshold: 0.4
  input_size: 1280 # Untuk CCTV, naikkan ke 1280 atau -1 (ukuran asli). Peringatan: Menurunkan FPS!

liveness:
  enabled: false 
  model_path: "models/2.7_80x80_MiniFASNetV2.onnx"
  threshold: 0.7

recognition:
  model_name: "buffalo_l" # Paket model InsightFace (berisi ArcFace)
  similarity_threshold: 0.55 # Sedikit lebih rendah untuk CCTV (wajah lebih buram)
  min_face_size: 40 # Diturunkan untuk mendeteksi wajah yang lebih jauh
  
tracking:
  enabled: true
  algorithm: "centroid" # Options: "centroid", "bytetrack" (masa depan)
  max_disappeared: 30 # Frame untuk menjaga ID tetap hidup tanpa deteksi
  distance_threshold: 50 # Jarak piksel untuk pencocokan centroid

attendance:
  cooldown_seconds: 30 # Abaikan orang yang sama selama X detik setelah log
  quality_threshold: 0.0 # Skor kualitas wajah minimum (jika tersedia) untuk diproses
  
storage:
  embeddings_path: "data/embeddings.json"
  logs_path: "data/attendance.csv"
  snapshots_path: "snapshots/"
  gallery_path: "gallery/"

ui:
  window_name: "Face Attendance System (Rebuild)"
  display_width: 960
  display_height: 540
  show_fps: true
  show_bbox: true
  show_landmarks: true
  font_scale: 0.6
```

## Penjelasan Setiap Bagian

### `system`
Pengaturan umum sistem.
-   **`mode`**: Mode operasi ("attendance" atau "enrollment").
-   **`gpu_enabled`**: Mengaktifkan akselerasi GPU (CUDA) jika tersedia.
-   **`debug_mode`**: Mengaktifkan mode debug untuk log yang lebih detail.
-   **`log_level`**: Tingkat logging (misal: "INFO", "DEBUG").

### `input`
Mengatur sumber video dan pemrosesan awal.
-   **`source`**: Sumber video. Bisa berupa integer (0, 1) untuk webcam atau string URL RTSP untuk IP Camera.
-   **`width`, `height`**: Resolusi target untuk stream.
-   **`reconnect_delay`**: Waktu tunggu (detik) sebelum mencoba menghubungkan kembali jika stream terputus.
-   **`preprocessing`**: Pengaturan untuk perbaikan kualitas gambar.
    -   **`enable_clahe`**: Mengaktifkan Contrast Limited Adaptive Histogram Equalization untuk memperbaiki pencahayaan yang buruk.

### `detection`
Pengaturan untuk model deteksi wajah.
-   **`model_name`**: Nama model yang digunakan (misal: "buffalo_l" untuk RetinaFace yang lebih akurat).
-   **`confidence_threshold`**: Batas minimal kepercayaan deteksi.
-   **`input_size`**: Ukuran input gambar untuk deteksi. Nilai lebih besar meningkatkan akurasi jarak jauh tapi menurunkan FPS.

### `liveness`
Pengaturan deteksi keaslian wajah (anti-spoofing).
-   **`enabled`**: Mengaktifkan atau menonaktifkan fitur liveness detection.
-   **`model_path`**: Path ke model ONNX liveness (MiniFASNetV2).
-   **`threshold`**: Batas skor untuk dianggap sebagai wajah asli.

### `recognition`
Pengaturan untuk pengenalan wajah.
-   **`model_name`**: Paket model InsightFace yang digunakan.
-   **`similarity_threshold`**: Batas kemiripan (cosine similarity) untuk mengenali wajah.
-   **`min_face_size`**: Ukuran wajah minimum (piksel) untuk diproses pengenalan.

### `tracking`
Pengaturan pelacakan objek (wajah).
-   **`algorithm`**: Algoritma tracking yang digunakan (saat ini "centroid").
-   **`max_disappeared`**: Jumlah frame maksimum sebuah ID dipertahankan jika wajah tidak terdeteksi.
-   **`distance_threshold`**: Jarak maksimum pergerakan wajah antar frame untuk dianggap sebagai orang yang sama.

### `attendance`
Logika pencatatan absensi.
-   **`cooldown_seconds`**: Jeda waktu sebelum orang yang sama bisa dicatat absensinya lagi.

### `storage`
Lokasi penyimpanan file data.
-   **`embeddings_path`**: File JSON database wajah.
-   **`logs_path`**: File CSV log absensi.
-   **`snapshots_path`**: Folder untuk menyimpan foto wajah saat absensi (jika diaktifkan).

### `ui`
Pengaturan tampilan antarmuka.
-   **`window_name`**: Judul jendela aplikasi.
-   **`display_width`, `display_height`**: Ukuran maksimum jendela tampilan. Frame kamera di-resize untuk display agar panel UI tetap terlihat penuh.
-   **`show_fps`**, **`show_bbox`**, **`show_landmarks`**: Toggle elemen visual.


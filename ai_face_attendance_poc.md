**Prompt: AI Agent Oneshot — Face Recognition Attendance PoC (Detil Eksekusi)**

**Ringkasan singkat tujuan**
Buat PoC lokal (offline) untuk absensi otomatis menggunakan pengenalan wajah dengan Python saja. Hasil akhir: satu skrip atau runner (`main.py`) yang menjalankan pipeline end-to-end: enroll → deteksi → embedding → matching → logging lokal. Fokus pada reproducibility, pengukuran akurasi, dan mitigasi spoofing dasar.

---

## 1. Konteks & Batasan
- Sistem dijalankan sepenuhnya lokal (no external API, no database).
- Input: webcam / USB camera.
- Output: file log lokal (`attendance.csv` / `attendance.jsonl`) + folder gallery lokal berstruktur.
- Agent harus bekerja oneshot: menerima prompt ini, men-generate satu artefak instruksi eksekusi lengkap (bukan kode) yang dapat langsung diikuti developer untuk implementasi. Jika diperlukan, agent boleh memberikan contoh format file (JSON/CSV) namun **tidak** boleh menulis atau mengeksekusi kode.

---

## 2. Tujuan Khusus yang Harus Dipenuhi Agent
1. Menyusun urutan tugas yang dapat dieksekusi oleh seorang engineer Python untuk membangun PoC.
2. Menjelaskan tiap komponen pipeline secara rinci (apa yang dilakukan, input/output, dependency minimal, parameter penting).
3. Menyediakan format file contoh (embeddings.json, attendance.csv, config.yaml) lengkap dengan contoh entry (maks 10 baris/objek) untuk referensi.
4. Menjelaskan prosedur enroll & verifikasi manual serta UX minimal melalui OpenCV window.
5. Menyusun protokol pengujian (test plan) lengkap: skenario, metrik, cara mengumpulkan metrik, cara menganalisis hasil, dan target awal.
6. Menyediakan checklist pra-deploy & mitigasi risiko (privasi, spoofing, bias).
7. Menyusun daftar dependensi Python yang disarankan (versi minimal) dan opsi alternatif yang ringan untuk edge/laptop.
8. Menyusun estimasi eksperimen lapangan 1 minggu: jumlah partisipan, jumlah pengulangan, dan laporan akhir yang harus dihasilkan.

---

## 3. Struktur Direktori yang Disarankan
```
/poc-face-attendance/
  gallery/                      # subfolder per-user: images untuk enroll
    user_001/
      img_001.jpg
      img_002.jpg
    user_002/
  embeddings.json                # JSON mapping user -> list of embeddings (float arrays)
  attendance.csv                 # CSV log absensi
  snapshots/                     # optional: snapshots untuk audit
  config.yaml                    # threshold, camera_id, params
  main.py                        # runner (not included in this prompt)
  README.md                      # instruksi run & eksperimen
```

---

## 4. Pipeline — Komponen & Deskripsi Detil
Setiap komponen berisi: tujuan, input, output, parameter penting, catatan implementasi.

### A. Capture Frame
- **Tujuan:** Mengambil frame dari camera secara kontinu.
- **Input:** device index / video path.
- **Output:** frame (BGR numpy array).
- **Parameter:** `camera_id`, `frame_width`, `frame_height`, `grab_every_n_frames`.
- **Catatan:** untuk performa, boleh hanya memproses setiap N-th frame (mis. tiap 2-3 frame).

### B. Face Detection & Alignment
- **Tujuan:** Deteksi bounding box wajah dan lakukan alignment landmark (mengoreksi rotasi/tengah wajah).
- **Input:** frame.
- **Output:** list{bbox, landmarks, aligned_face_image}.
- **Parameter:** `min_face_size`, `detection_conf_threshold`, `max_faces`.
- **Pilihan implementasi (PoC):** MTCNN (mudah pakai), dlib HOG (cepat), RetinaFace (akurasi). Untuk PoC, pilih yang cepat dan stabil pada laptop, mis. `MTCNN` atau `dlib`.

### C. Liveness (PoC ringan)
- **Tujuan:** Menurunkan risiko spoofing foto/video.
- **Input:** sequence kecil frame yang berisi wajah terdeteksi dan landmark per-frame.
- **Output:** boolean `liveness_passed`, `liveness_score`.
- **Strategi PoC:**
  - **Blink detection:** periksa perubahan landmark mata selama window T (mis. 10-20 frame) untuk mendeteksi kedipan.
  - **Head-movement check:** kecilkan optical flow / perubahan posisi kepala antar frame.
  - **Challenge-response (opsional manual):** minta subjek mengangguk/senyum lalu deteksi perubahan ekspresi.
- **Catatan:** jelaskan false-negatives risiko; challenge-response menambah akurasi tapi mengurangi kenyamanan.

### D. Embedding Extraction
- **Tujuan:** Mengonversi wajah yang teralign ke vektor embedding numerik fixed-length.
- **Input:** aligned_face_image.
- **Output:** embedding vector (float32 array, seperti 512-dim atau 128-dim tergantung model).
- **Parameter:** `model_name`, `embedding_dim`, `normalize`.
- **Pilihan model PoC:** facenet-pytorch (128-dim), InsightFace (512-dim), MobileFaceNet (128-dim). Untuk kecepatan di laptop/RPi: gunakan model ringan atau ONNX-exported model via `onnxruntime`.

### E. Matching
- **Tujuan:** Membandingkan embedding input dengan gallery lokal dan menentukan match.
- **Input:** query_embedding, embeddings.json (gallery embeddings per user).
- **Output:** match{user_id, score}, or `unknown`.
- **Algoritma:** L2-normalize embedding → cosine similarity (dot product) atau Euclidean distance.
- **Strategi multi-embedding per-user:** simpan list embeddings; matching = max(similarity) atau mean similarity; juga dapat gunakan min-distance.
- **Parameter:** `distance_metric` (cosine/euclidean), `threshold_match`.
- **Threshold awal (guideline):** untuk cosine similarity, mulai dari 0.62–0.80 (model tergantung). Agent harus menyarankan kalibrasi pasca-collect data.

### F. Logging
- **Tujuan:** Menyimpan event absensi ke file lokal untuk audit & analisis.
- **Format:** CSV atau JSONL.
- **Fields minimal:** `timestamp_iso, user_id, user_name, matched_score, liveness_passed, snapshot_path, note`
- **Kebijakan snapshot:** simpan snapshot hanya jika `matched_score` > `save_snapshot_threshold` atau jika `unknown` untuk audit.

### G. UI Minimal (OpenCV overlay)
- **Tujuan:** Berikan feedback real-time.
- **Elemen:** bounding box, nama atau "Unknown", confidence bar, liveness icon, tombol keyboard: `e`=enroll, `q`=quit, `s`=save snapshot.
- **Catatan UX:** jangan tampilkan raw embeddings atau info sensitif. Tambahkan clear text bahwa ini PoC dan data lokal.

---

## 5. Contoh Format File (Contoh entries)

### embeddings.json (contoh singkat)
```json
{
  "user_001": {
    "name": "Asep",
    "embeddings": [[0.0123, -0.234, ...], [0.015, -0.230, ...]],
    "meta": {"enrolled_at": "2025-11-11T12:00:00Z", "notes": "10 images"}
  },
  "user_002": {
    "name": "Budi",
    "embeddings": [[0.101, -0.05, ...]]
  }
}
```

> Catatan: embeding vectors dipersingkat di contoh. Simpan sebagai arrays float (JSON) atau `.npy` untuk performa lebih baik.

### attendance.csv (kolom & contoh baris)
```
timestamp_iso,user_id,user_name,matched_score,liveness_passed,snapshot_path,note
2025-11-11T07:55:12Z,user_001,Asep,0.78,True,snap_001.jpg,auto
2025-11-11T07:55:34Z,,Unknown,0.31,False,,no_match
```

### config.yaml (contoh parameter penting)
```yaml
camera_id: 0
frame_width: 1280
frame_height: 720
grab_every_n_frames: 2
detection_conf_threshold: 0.6
min_face_size: 40
model_name: "facenet-pytorch"
distance_metric: "cosine"
threshold_match: 0.70
save_snapshot_threshold: 0.75
embeddings_path: "embeddings.json"
log_path: "attendance.csv"
```

---

## 6. Mode Enroll (Workflows & Tips)
1. **CLI-driven enroll:** tekan `e` saat wajah terdeteksi → capture 10–20 frames / variasi sudut → simpan images ke `gallery/user_xxx/`.
2. **Batch embedding extraction:** setelah capture, jalankan routine yang menghitung embedding tiap image lalu simpan ke `embeddings.json`.
3. **Data augmentasi (opsional):** brightness/contrast variations, mild rotations untuk robustness.
4. **Meta & consent:** buat `consent.txt` di folder user yang menyatakan persetujuan enroll untuk PoC.

---

## 7. Protokol Pengujian & Eksperimen (1 minggu, detil)
Tujuan: kumpulkan data untuk mengkalibrasi threshold & menghitung metrik.

### Rencana eksperimen 7 hari (contingency untuk PoC):
- **Partisipan:** 20 orang.
- **Enrolled images per orang:** 20 (variasi sudut & lighting).
- **Skenario uji:**
  1. Normal indoor light, jarak 1m.
  2. Backlit (sinar datang dari belakang), jarak 1m.
  3. With mask, partial occlusion.
  4. With hat/glasses.
  5. Moving/walking past camera (simulate gate).
- **Repetisi:** 10 pass per skenario per orang.

### Data yang dikumpulkan:
- logs CSV lengkap
- snapshots untuk kasus `unknown` dan `mis-id`
- per-frame latency (ms) and FPS

### Metrik & analisis:
- **TPR (True Positive Rate):** jumlah correct matches / jumlah actual presents.
- **FAR (False Accept Rate):** jumlah false matches / jumlah attempts from impostors.
- **FRR (False Reject Rate):** jumlah fails for enrolled users.
- **Latency:** avg ms per detection + 95th percentile.

### Kalibrasi threshold:
- Hitung similarity distribusi intra-person vs inter-person.
- Pilih threshold yang meminimalkan FAR pada tingkat FRR yang masih bisa diterima; tunjukkan grafik histogram distribusi similarity.

---

## 8. Metrik Logging & Analisis Otomatis (apa agent harus keluarkan)
Agent harus men-generate instruksi untuk script analisis sederhana (bukan kode):
- cara parsing `attendance.csv` untuk menghitung TPR/FAR/FRR
- cara membuat histogram similarity intra vs inter
- cara mengekstrak kasus-kasus failure (mis-ID) ke folder `failure_cases/` untuk review manual

---

## 9. Checklist Keamanan & Privasi (PoC lokal)
- [ ] Simpan embeddings alih-alih raw images bila memungkinkan.
- [ ] Simpan consent file untuk tiap user.
- [ ] Enkripsi file sensitif jika perangkat mudah hilang.
- [ ] Hapus snapshot otomatis setelah retention period (mis. 7 hari).
- [ ] Catat siapa yang punya akses ke laptop/edge device.
- [ ] Dokumentasikan bahwa ini PoC dan jangan sebarkan publik.

---

## 10. Mitigasi Spoofing & Bias
- **Spoofing:** tambahkan blink detection / head-movement challenge; simpan foto audit untuk review.
- **Bias:** pastikan enroll dataset beragam (usia, etnis, pencahayaan). Saat menganalisis, bandingkan TPR per-subgroup.

---

## 11. Dependensi Python & Versi Rekomendasi
- Python 3.9+ (3.10 atau 3.11 lebih baik)
- numpy >= 1.22
- opencv-python >= 4.5
- facenet-pytorch OR insightface OR onnxruntime (pilih salah satu)
- scipy >= 1.7 (opsional for distances)
- imutils (opsional)
- dlib (opsional, jika menggunakan dlib)

> Catatan: jika target hardware Raspberry Pi, pertimbangkan ONNX + `onnxruntime` dan model quantized; atau gunakan `tflite` jika model tersedia.

---

## 12. Troubleshooting Umum & Cara Tindakan
- **Detektor sering miss face:** turunkan `min_face_size`, tingkatkan resolusi frame, atau ganti detector.
- **Banyak false positives:** naikkan `detection_conf_threshold`.
- **Mis-identification sering terjadi:** tambah lebih banyak foto enroll; gunakan multiple embeddings per-user; perbaiki alignment.
- **Latency tinggi:** proses tiap N-th frame, pakai ONNX, kurangi input resolution.

---

## 13. Deliverables yang Diharapkan dari Agent Oneshot
Agent harus menghasilkan (dokumen/instruksi):
1. Dokumen langkah-langkah eksekusi rinci (ini termasuk struktur folder, file contoh, dan config.yaml contoh). 
2. Prosedur enroll & uji lapangan terperinci.
3. Format log & contoh entry.
4. Checklist keamanan & mitigasi risiko.
5. Protokol kalibrasi threshold dan analisis metrik.

Agent **tidak** boleh menulis kode eksekusi; hanya berikan instruksi, format file contoh, dan rencana operasi.

---

## 14. Output yang Diminta dari Agent (saat oneshot dijalankan)
Agent harus kembali dengan satu artefak dokumentasi yang memuat semua bagian di atas dalam bahasa Indonesia. Dokumentasi harus ringkas namun mencakup semua instruksi teknis yang dapat langsung diikuti oleh engineer Python untuk implementasi PoC.

---

Jika sudah paham, tugas berikutnya: setelah kamu minta, aku bisa memecah dokumentasi ini ke dalam checklist step-by-step untuk tiap fungsi (enroll, detect loop, matching, logging) — masih tanpa menulis kode. Mau aku pecah ke checklist itu sekarang?


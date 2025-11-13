# Face Recognition Attendance PoC

## Overview

This is a complete offline face recognition attendance system built with Python. It provides a proof-of-concept for automatic attendance tracking using face detection, liveness detection, and face recognition. The system is designed to run entirely locally without requiring external APIs or databases.

## Features

- **Face Detection & Alignment**: MTCNN-based face detection with facial landmark alignment
- **Liveness Detection**: Anti-spoofing measures including blink detection and head movement analysis
- **Face Recognition**: FaceNet-based embedding extraction and matching
- **Real-time UI**: OpenCV-based interface with real-time feedback
- **Enrollment System**: Tools for enrolling new users and managing the gallery
- **Attendance Logging**: CSV/JSONL logging with snapshot storage
- **Testing & Analytics**: Tools for performance analysis and threshold calibration
- **Local Storage**: All data stored locally (embeddings, logs, images)

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Camera Feed   │ -> │ Face Detection  │ -> │ Liveness Check  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                v                        v
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Face Alignment  │    │ Frame Analysis  │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                v                        v
                       ┌─────────────────┐    ┌─────────────────┐
                       │Embedding Extract│    │ Spoof Detection │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                v                        v
                       ┌─────────────────┐               │
                       │  Face Matching  │               │
                       └─────────────────┘               │
                                │                        │
                                v                        v
                       ┌─────────────────┐      ┌─────────────────┐
                       │  Attendance Log │      │  Snapshot Save  │
                       └─────────────────┘      └─────────────────┘
```

## File Structure

```
poc-face-attendance/
├── main.py                 # Main application runner
├── config.yaml            # System configuration
├── requirements.txt       # Python dependencies
├── face_detection.py      # Face detection component
├── liveness_detection.py  # Liveness detection component
├── embedding_extractor.py # Face embedding extraction
├── matching_engine.py     # Face matching and identification
├── logging_system.py      # Attendance logging
├── ui_system.py          # User interface
├── enrollment_tool.py    # User enrollment utilities
├── testing_tool.py       # Testing and analytics
├── embeddings.json       # User gallery (auto-generated)
├── attendance.csv        # Attendance logs (auto-generated)
├── gallery/              # User enrollment images
│   ├── user_001/
│   └── user_002/
└── snapshots/            # Attendance snapshots
```

## Installation

### Prerequisites

- Python 3.9 or higher
- USB/built-in camera
- At least 2GB RAM recommended
- Windows/Linux/macOS

### Setup

1. **Install Python dependencies:**

   ```bash
   cd poc-face-attendance
   pip install -r requirements.txt
   ```

2. **System will create directories automatically:**
   - `gallery/` - for user enrollment images
   - `snapshots/` - for attendance snapshots

3. **Configure system (optional):**
   - Edit `config.yaml` to adjust parameters
   - See Configuration section for details

## Usage

### Starting the System

```bash
python main.py
```

### Main Interface

The system opens a real-time window showing:

- **Live camera feed** with face detection boxes
- **User identification** status and match scores
- **Liveness detection** indicators
- **System status** and performance metrics

### Keyboard Controls

| Key | Action |
|-----|--------|
| `E` | Start enrollment mode |
| `S` | Save manual snapshot |
| `R` | Reset detection |
| `H` | Show help dialog |
| `Q` | Quit application |

### Enrollment Process

#### Real-time Enrollment

```bash
python enrollment_tool.py --mode realtime --user-id user_001 --user-name "John Doe" --num-images 20
```

#### Batch Enrollment (from existing images)

```bash
python enrollment_tool.py --mode batch --user-id user_002 --user-name "Jane Smith" --image-dir ./user_images
```

#### Managing Enrolled Users

```bash
# List all users
python enrollment_tool.py --mode list

# Remove user
python enrollment_tool.py --mode remove --user-id user_001

# Export user data
python enrollment_tool.py --mode export --output users_backup.json
```

### Testing and Analytics

#### Generate Performance Report

```bash
python testing_tool.py --mode report --output performance_report.html
```

#### Analyze Attendance Logs

```bash
python testing_tool.py --mode analyze --log-path attendance.csv
```

#### Calibrate Matching Threshold

```bash
python testing_tool.py --mode calibrate --target-far 0.01
```

#### Export Test Results

```bash
python testing_tool.py --mode export --output test_results.json
```

## Configuration

Edit `config.yaml` to customize system behavior:

### Camera Settings

```yaml
camera_id: 0          # USB camera index (0=default)
frame_width: 1280     # Camera resolution
frame_height: 720
grab_every_n_frames: 2 # Process every N frames for performance
```

### Face Detection

```yaml
detection_conf_threshold: 0.6  # Minimum confidence for detection
min_face_size: 40             # Minimum face size in pixels
```

### Recognition Settings

```yaml
model_name: "vgg_face2"     # FaceNet model variant
distance_metric: "cosine"   # Distance metric
threshold_match: 0.70       # Match threshold (0.5-0.9)
```

### Liveness Detection

```yaml
liveness_required: true          # Require liveness check
liveness_window_size: 20         # Analysis window
liveness_blink_threshold: 0.3    # Blink detection sensitivity
```

### File Paths

```yaml
embeddings_path: "embeddings.json"  # User gallery storage
log_path: "attendance.csv"          # Attendance log file
snapshot_dir: "snapshots"           # Snapshot storage
gallery_dir: "gallery"              # Enrollment images
```

## Performance and Metrics

### Target Performance

- **Processing Speed**: 5-15 FPS (depending on hardware)
- **Detection Accuracy**: >95% for enrolled faces
- **Liveness Detection**: >90% accuracy against photos
- **Memory Usage**: <500MB typical usage

### Key Metrics Tracked

- **TPR (True Positive Rate)**: Correct matches / Total actual users
- **FAR (False Accept Rate)**: False matches / Total attempts
- **FRR (False Reject Rate)**: Failed matches / Total enrolled users
- **Processing Latency**: Average and 95th percentile processing time

### Performance Analysis

The system provides detailed analytics:

- Similarity score distributions
- Threshold optimization
- Daily attendance patterns
- Processing time statistics

## Security and Privacy

### Data Storage

- **Embeddings**: Stored locally in JSON format (not raw images)
- **Attendance Logs**: CSV format with timestamps and scores
- **Snapshots**: JPEG images stored locally only
- **No External Data**: All processing happens locally

### Spoofing Prevention

- **Liveness Detection**: Blink detection and head movement analysis
- **Frame Consistency**: Temporal analysis of face detection
- **Texture Analysis**: Detection of printed photos
- **Challenge Response**: Optional user interaction verification

### Privacy Considerations

- No biometric data transmitted externally
- Local-only processing and storage
- User consent required for enrollment
- Configurable data retention periods

## Troubleshooting

### Common Issues

**Camera not detected:**

```bash
# Check camera index
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Try different camera index in config.yaml
camera_id: 1  # or 2, etc.
```

**No faces detected:**

- Ensure good lighting conditions
- Adjust `min_face_size` in config
- Check camera resolution settings
- Verify face is clearly visible

**Poor recognition accuracy:**

- Increase enrollment images (20+ recommended)
- Ensure diverse enrollment angles
- Check lighting consistency
- Calibrate threshold using testing tool

**High processing latency:**

- Increase `grab_every_n_frames` in config
- Reduce camera resolution
- Consider using GPU acceleration
- Close other applications

### Log Analysis

Check `attendance.csv` for detailed system behavior:

```bash
# View recent logs
tail -f attendance.csv

# Count successful matches
grep "user_" attendance.csv | wc -l
```

## Development

### Adding New Features

The system is modular with clear component boundaries:

- `face_detection.py`: Face detection logic
- `liveness_detection.py`: Anti-spoofing measures
- `embedding_extractor.py`: Feature extraction
- `matching_engine.py`: Recognition algorithms
- `ui_system.py`: User interface
- `logging_system.py`: Data persistence

### Extending the System

- Add new liveness detection methods
- Implement different face recognition models
- Add support for multiple cameras
- Create web-based interface
- Add database integration

### Testing

```bash
# Test individual components
python face_detection.py
python embedding_extractor.py
python matching_engine.py

# Run comprehensive tests
python testing_tool.py --mode analyze
```

## API Reference

### Core Classes

#### FaceAttendanceSystem

Main system orchestrator

```python
system = FaceAttendanceSystem("config.yaml")
system.start()  # Begin processing
```

#### FaceDetector

Face detection and alignment

```python
detector = FaceDetector(min_face_size=40, detection_conf_threshold=0.6)
faces = detector.process_frame(frame)
```

#### MatchingEngine

Face recognition and identification

```python
engine = MatchingEngine(embedding_manager, threshold_match=0.70)
result = engine.match_single_embedding(embedding)
```

#### EnrollmentTool

User enrollment utilities

```python
tool = EnrollmentTool()
result = tool.enroll_user_realtime("user_001", "John Doe", 20)
```

## License

This is a proof-of-concept system for educational and research purposes. Do not use in production environments without proper security auditing and legal compliance.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the configuration options
3. Examine the logs in `attendance.csv`
4. Test individual components

---

**Note**: This is a proof-of-concept system. For production use, additional security measures, performance optimization, and legal compliance considerations are required.

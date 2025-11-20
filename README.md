# Face Attendance System

A robust and efficient Face Attendance System built with Python, utilizing state-of-the-art computer vision libraries including InsightFace and YOLOv8 (via InsightFace) for accurate face detection and recognition.

## Purpose

This project aims to provide a scalable and easy-to-deploy solution for automated attendance tracking. It uses facial recognition to identify individuals in real-time video streams (Webcam or RTSP) and logs their attendance with timestamping and anti-spam cooldowns.

## Features

*   **Real-time Face Detection**: Uses high-performance RetinaFace models.
*   **Accurate Face Recognition**: Leverages ArcFace embeddings for reliable identity verification.
*   **Multi-Object Tracking**: Implements Centroid Tracking to maintain identity across frames and reduce redundant processing.
*   **Anti-Spoofing / Cooldown**: Prevents multiple logs for the same person within a configurable time window.
*   **User Enrollment Tool**: Interactive tool to easily capture and register new users.
*   **Cross-Platform**: Works on Windows and Linux.
*   **GPU Acceleration**: Supports CUDA for NVIDIA GPUs for high-speed processing.

## Prerequisites

*   **Python 3.8+**
*   **C++ Build Tools** (needed for some dependencies like `insightface`)
*   **NVIDIA Drivers & CUDA Toolkit** (Optional, for GPU support)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/face-attendance-system.git
cd face-attendance-system
```

### 2. Install Dependencies
It is recommended to use a virtual environment.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Edit `config.yaml` to customize the system behavior. Key settings include:

*   **Input Source**: Set `input.source` to `0` for webcam or an RTSP URL for IP cameras.
*   **Detection Model**: Choose between `buffalo_l` (more accurate) or `buffalo_s` (faster).
*   **Thresholds**: Adjust `confidence_threshold` and `similarity_threshold` to balance between false positives and false negatives.

## Usage

### Launching the System
You can use the provided launcher scripts for an easy menu-driven interface.

**Windows:**
Double-click `run.bat` or run:
```powershell
.\run.bat
```

**Linux:**
Run the shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Execution

**Start Attendance System:**
```bash
python main.py
```

**Enroll a New User:**
```bash
python enrollment_tool.py --id 1001 --name "John Doe" --samples 10
```

## Project Structure

*   `core/`: Contains the core logic modules (Detection, Recognition, Tracking, UI).
*   `data/`: Stores generated data like logs (`attendance.csv`) and user embeddings (`embeddings.json`).
*   `scripts/`: Utility scripts for verification.
*   `main.py`: Entry point for the attendance system.
*   `enrollment_tool.py`: Script for registering new users.
*   `launch.py`: Cross-platform launcher script.
*   `config.yaml`: Central configuration file.

## Troubleshooting

*   **Visual C++ Error**: If you encounter errors installing `insightface` or `onnxruntime`, ensure you have the Visual C++ Redistributable installed.
*   **GPU Not Used**: Check if `onnxruntime-gpu` is installed and compatible with your CUDA version. You can force CPU mode in `config.yaml` by setting `gpu_enabled: false`.

## License

MIT License

import os
import urllib.request
import sys
from pathlib import Path

def download_file(url, dest_path):
    print(f"Downloading {url}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"Saved to {dest_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def setup_liveness_model():
    # Create models directory if it doesn't exist
    root_dir = Path(__file__).parent.parent
    models_dir = root_dir / "models"
    models_dir.mkdir(exist_ok=True)

    model_name = "2.7_80x80_MiniFASNetV2.onnx"
    target_path = models_dir / model_name

    if not target_path.exists():
        print(f"Liveness model not found at {target_path}")
        # Using a common source for MiniFASNetV2
        url = "https://github.com/MinhTran12/MiniFASNet/raw/master/weights/2.7_80x80_MiniFASNetV2.onnx"
        download_file(url, str(target_path))
    else:
        print(f"Liveness model already exists: {target_path}")

def setup_insightface_models():
    print("\nChecking/Downloading InsightFace models (buffalo_l)...")
    try:
        import insightface
        # Initializing FaceAnalysis triggers the download if not present
        app = insightface.app.FaceAnalysis(name='buffalo_l', root='~/.insightface')
        app.prepare(ctx_id=-1) # ctx_id=-1 means CPU
        print("InsightFace 'buffalo_l' models are ready.")
    except ImportError:
        print("Error: 'insightface' library not installed. Run 'pip install insightface'")
    except Exception as e:
        print(f"Error setting up InsightFace models: {e}")

if __name__ == "__main__":
    print("=== Setting up Models for Benchmark ===")
    setup_liveness_model()
    setup_insightface_models()
    print("\nSetup complete! You can now run 'python bench.py'")

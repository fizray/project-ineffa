import cv2
import numpy as np
import json
import os
import yaml
import logging
import argparse
from datetime import datetime
from insightface.app import FaceAnalysis

from core.face_detection import FaceDetector
from core.embedding_extractor import RecognitionEngine

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Enrollment")

class EnrollmentSystem:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self.embeddings_path = self.config['storage']['embeddings_path']
        
        # Initialize InsightFace
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.config['system']['gpu_enabled'] else ['CPUExecutionProvider']
        logger.info(f"Initializing InsightFace with providers: {providers}")
        
        self.insightface_app = FaceAnalysis(
            name=self.config['detection']['model_name'], 
            allowed_modules=['detection', 'recognition'], 
            providers=providers
        )
        self.insightface_app.prepare(ctx_id=0, det_size=(self.config['detection']['input_size'], self.config['detection']['input_size']))
        
        self.detector = FaceDetector(
            app=self.insightface_app,
            conf_threshold=self.config['detection']['confidence_threshold'],
            nms_threshold=self.config['detection']['nms_threshold']
        )
        
        self.recognizer = RecognitionEngine(
            app=self.insightface_app
        )
        
        self.known_embeddings = {}
        self._load_embeddings()

    def _load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_embeddings(self):
        if os.path.exists(self.embeddings_path):
            try:
                with open(self.embeddings_path, 'r') as f:
                    self.known_embeddings = json.load(f)
                logger.info(f"Loaded {len(self.known_embeddings)} users.")
            except Exception as e:
                logger.error(f"Failed to load embeddings: {e}")
                self.known_embeddings = {}
        else:
            self.known_embeddings = {}

    def _save_embeddings(self):
        try:
            # Convert numpy arrays to lists for JSON serialization if needed
            # But we store them as lists in memory for this tool to be safe
            with open(self.embeddings_path, 'w') as f:
                json.dump(self.known_embeddings, f, indent=2)
            logger.info(f"Saved embeddings to {self.embeddings_path}")
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")

    def enroll_user(self, user_id, user_name, num_samples=5):
        cap = cv2.VideoCapture(self.config['input']['source'])
        if not cap.isOpened():
            logger.error("Cannot open camera")
            return

        logger.info(f"Starting enrollment for {user_name} (ID: {user_id})")
        logger.info(f"Please look at the camera. We need {num_samples} good samples.")
        logger.info("Press 'c' to capture a sample, 'q' to quit.")

        collected_embeddings = []
        
        while len(collected_embeddings) < num_samples:
            ret, frame = cap.read()
            if not ret:
                break

            display_frame = frame.copy()
            faces = self.detector.detect(frame)

            status_color = (0, 0, 255) # Red
            status_text = "No Face"

            if len(faces) == 0:
                status_text = "No Face Detected"
            elif len(faces) > 1:
                status_text = "Multiple Faces! One only."
            else:
                face = faces[0]
                bbox = face.bbox.astype(int)
                
                # Quality Checks
                h = bbox[3] - bbox[1]
                w = bbox[2] - bbox[0]
                
                if h < self.config['recognition']['min_face_size']:
                    status_text = "Too Far / Small"
                else:
                    status_text = "Ready to Capture (Press 'c')"
                    status_color = (0, 255, 0) # Green
                    cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), status_color, 2)

            # UI Overlay
            cv2.putText(display_frame, f"User: {user_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Samples: {len(collected_embeddings)}/{num_samples}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, status_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

            cv2.imshow("Enrollment", display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('c'):
                if len(faces) == 1 and status_color == (0, 255, 0):
                    embedding = self.recognizer.get_embedding(frame, faces[0])
                    if embedding is not None:
                        collected_embeddings.append(embedding.tolist()) # Store as list
                        logger.info(f"Captured sample {len(collected_embeddings)}/{num_samples}")
                    else:
                        logger.warning("Failed to extract embedding")

        cap.release()
        cv2.destroyAllWindows()

        if len(collected_embeddings) >= num_samples:
            # Save to memory
            if user_id not in self.known_embeddings:
                self.known_embeddings[user_id] = {
                    "name": user_name,
                    "embeddings": []
                }
            
            self.known_embeddings[user_id]["embeddings"].extend(collected_embeddings)
            self.known_embeddings[user_id]["updated_at"] = datetime.now().isoformat()
            
            self._save_embeddings()
            logger.info(f"Successfully enrolled {user_name} with {len(collected_embeddings)} new samples.")
        else:
            logger.warning("Enrollment cancelled or incomplete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrollment Tool")
    parser.add_argument("--id", type=str, required=True, help="Unique User ID")
    parser.add_argument("--name", type=str, required=True, help="User Display Name")
    parser.add_argument("--samples", type=int, default=5, help="Number of samples to collect")
    
    args = parser.parse_args()
    
    system = EnrollmentSystem()
    system.enroll_user(args.id, args.name, args.samples)

import cv2
import yaml
import time
import logging
import numpy as np
import json
import os
from datetime import datetime

from core.stream_loader import RTSPStreamLoader
from core.face_detection import FaceDetector
from core.embedding_extractor import RecognitionEngine
from core.tracker import CentroidTracker
from core.ui_system import UISystem
from insightface.app import FaceAnalysis
from numpy.linalg import norm

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")

class AttendanceSystem:
    """
    The main application class for the Face Attendance System.
    Manages video streaming, face detection, recognition, tracking, and logging.
    """
    def __init__(self, config_path="config.yaml"):
        """
        Initializes the AttendanceSystem.

        Args:
            config_path (str): Path to the configuration YAML file.
        """
        self.config = self._load_config(config_path)

        # Initialize Modules
        self.ui = UISystem(self.config)
        self.stream = RTSPStreamLoader(
            source=self.config['input']['source'],
            width=self.config['input']['width'],
            height=self.config['input']['height'],
            reconnect_delay=self.config['input']['reconnect_delay']
        )

        # Initialize Shared InsightFace App
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

        self.tracker = CentroidTracker(
            max_disappeared=self.config['tracking']['max_disappeared'],
            max_distance=self.config['tracking']['distance_threshold']
        )

        # State
        self.known_face_encodings = [] # Matrix (N, 512)
        self.known_face_names = []     # List of N names
        self.attendance_log = {} # {name: last_seen_timestamp}
        self.recent_logs = [] # List of {'name': str, 'time': str} for UI
        self.tracked_faces_state = {} # {object_id: {'name': str, 'processed': bool, 'best_score': float}}

        self._load_embeddings()

    def _load_config(self, path):
        """
        Loads the YAML configuration file.

        Args:
            path (str): Path to the YAML file.

        Returns:
            dict: Parsed configuration.
        """
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_embeddings(self):
        """
        Loads known face embeddings from the JSON storage file.
        Populates self.known_face_encodings and self.known_face_names.
        """
        path = self.config['storage']['embeddings_path']
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)

                encodings = []
                names = []

                for user_id, user_data in data.items():
                    name = user_data.get('name', 'Unknown')
                    embeddings = user_data.get('embeddings', [])
                    for embed in embeddings:
                        # Normalize embedding on load
                        emb_array = np.array(embed, dtype=np.float32)
                        norm_val = norm(emb_array)
                        if norm_val > 0:
                            emb_array = emb_array / norm_val

                        encodings.append(emb_array)
                        names.append(name)

                self.known_face_encodings = np.array(encodings)
                self.known_face_names = names

                logger.info(f"Loaded {len(self.known_face_encodings)} embeddings from {len(data)} users.")
            except Exception as e:
                logger.error(f"Failed to load embeddings: {e}")
        else:
            logger.warning("No embeddings file found. Starting empty.")

    def _identify_face(self, embedding):
        """
        Identifies a face by comparing its embedding against known embeddings.

        Args:
            embedding (numpy.ndarray): The query face embedding.

        Returns:
            tuple: (name, score) where name is the best matching name (or "Unknown")
                   and score is the similarity score.
        """
        if len(self.known_face_encodings) == 0:
            return "Unknown", 0.0

        # Normalize query embedding
        norm_val = norm(embedding)
        if norm_val > 0:
            embedding = embedding / norm_val

        # Vectorized Cosine Similarity
        # (N, 512) dot (512,) -> (N,)
        similarities = np.dot(self.known_face_encodings, embedding)

        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        if best_score >= self.config['recognition']['similarity_threshold']:
            return self.known_face_names[best_idx], float(best_score)

        return "Unknown", float(best_score)

    def _log_attendance(self, name):
        """
        Logs attendance for a recognized user.
        Handles cooldowns to prevent spamming logs for the same person.

        Args:
            name (str): The name of the recognized user.

        Returns:
            bool: True if attendance was logged, False if ignored (cooldown or error).
        """
        now = time.time()
        cooldown = self.config['attendance']['cooldown_seconds']

        if name in self.attendance_log:
            last_seen = self.attendance_log[name]
            if now - last_seen < cooldown:
                return False # Cooldown active

        self.attendance_log[name] = now

        # Write to CSV
        log_path = self.config['storage']['logs_path']
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_only_str = datetime.now().strftime("%H:%M:%S")

        # Update UI Log
        self.recent_logs.append({'name': name, 'time': time_only_str})
        if len(self.recent_logs) > 20:
            self.recent_logs.pop(0)

        # Simple append (in production, use a proper logger or DB)
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f:
                f.write(f"{timestamp_str},{name}\n")
            logger.info(f"ATTENDANCE LOGGED: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
            return False

    def run(self):
        """
        Starts the main application loop.
        Captures frames, detects faces, tracks them, recognizes them, and updates the UI.
        """
        self.stream.start()
        logger.info("System Started. Press 'q' to exit.")

        try:
            while True:
                frame = self.stream.read()
                if frame is None:
                    continue

                # 1. Detection
                faces = self.detector.detect(frame)

                # Prepare rects for tracker
                rects = []
                for face in faces:
                    rects.append(face.bbox.astype(int))

                # 2. Tracking
                objects = self.tracker.update(rects)

                # Map tracker IDs back to face objects
                # This is a heuristic mapping since tracker only knows centroids/rects
                # We find the face object closest to the tracked centroid

                current_tracked_ids = set(objects.keys())
                faces_map = {} # {object_id: face_object} for UI drawing

                # Clean up state for lost objects
                for oid in list(self.tracked_faces_state.keys()):
                    if oid not in current_tracked_ids:
                        del self.tracked_faces_state[oid]

                for object_id, centroid in objects.items():
                    # Find the corresponding face object
                    best_face = None
                    min_dist = float('inf')

                    for face in faces:
                        # Calculate face centroid
                        bbox = face.bbox
                        cX = (bbox[0] + bbox[2]) / 2
                        cY = (bbox[1] + bbox[3]) / 2
                        dist = np.linalg.norm(np.array([cX, cY]) - centroid)

                        if dist < self.config['tracking']['distance_threshold']:
                            if dist < min_dist:
                                min_dist = dist
                                best_face = face

                    if best_face:
                        faces_map[object_id] = best_face
                        # Initialize state for new ID
                        if object_id not in self.tracked_faces_state:
                            self.tracked_faces_state[object_id] = {
                                'name': "Unknown",
                                'processed': False,
                                'best_score': 0.0,
                                'history_count': 0
                            }

                        state = self.tracked_faces_state[object_id]
                        state['history_count'] += 1

                        # 3. Smart Recognition Logic
                        # Only recognize if:
                        # - Not yet processed (or Unknown)
                        # - Face quality is good (size check)
                        # - We haven't tried too many times (optional)

                        face_height = best_face.bbox[3] - best_face.bbox[1]

                        if not state['processed'] or state['name'] == "Unknown":
                            if face_height >= self.config['recognition']['min_face_size']:
                                # Extract Embedding
                                embedding = self.recognizer.get_embedding(frame, best_face)
                                if embedding is not None:
                                    name, score = self._identify_face(embedding)

                                    if name != "Unknown":
                                        state['name'] = name
                                        state['best_score'] = score
                                        state['processed'] = True
                                        self._log_attendance(name)
                                    else:
                                        # Keep trying if unknown, maybe better angle comes up
                                        # But don't spam recognition every frame if it's clearly unknown
                                        pass

                # Display
                frame = self.ui.draw_dashboard(frame, self.tracked_faces_state, faces_map, self.recent_logs, is_connected=True)

                cv2.imshow(self.config['ui']['window_name'], frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            pass
        finally:
            self.stream.stop()
            cv2.destroyAllWindows()
            logger.info("System Stopped.")

if __name__ == "__main__":
    system = AttendanceSystem()
    system.run()

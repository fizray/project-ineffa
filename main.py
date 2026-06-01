import sys
import os

# Pre-flight Check: Ensure NumPy < 2.0.0 for OpenCV compatibility
try:
    import numpy as np
    if np.__version__.startswith('2.'):
        print("\n" + "!"*60)
        print(f" [CRITICAL] Incompatible NumPy version detected: {np.__version__}")
        print(" OpenCV requires NumPy 1.x to function correctly.")
        print("!"*60)
        print(" FIX: Run 'pip install \"numpy<2.0.0\"' to downgrade.")
        print("!"*60 + "\n")
        sys.exit(1)
except ImportError:
    pass

import cv2
import yaml
import time
import logging
# import numpy as np # Already imported above
import json
from datetime import datetime

from core.stream_loader import RTSPStreamLoader
from core.face_detection import FaceDetector
from core.liveness_detector import LivenessDetector
from core.embedding_extractor import RecognitionEngine
from core.tracker import CentroidTracker
from core.ui_system import UISystem
from core.attendance_manager import AttendanceManager
from insightface.app import FaceAnalysis
from numpy.linalg import norm

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Main")

class AttendanceSystem:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        
        # Initialize Modules
        self.ui = UISystem(self.config)
        self.attendance_manager = AttendanceManager(self.config)
        self.stream = RTSPStreamLoader(
            source=self.config['input']['source'],
            width=self.config['input']['width'],
            height=self.config['input']['height'],
            reconnect_delay=self.config['input']['reconnect_delay']
        )
        
        self._init_insightface()
        
        self.detector = FaceDetector(
            app=self.insightface_app,
            conf_threshold=self.config['detection']['confidence_threshold'],
            nms_threshold=self.config['detection']['nms_threshold']
        )
        
        self.liveness_detector = LivenessDetector(self.config)

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
        self.tracked_faces_state = {} # {object_id: {'name': str, 'processed': bool, 'best_score': float}}
        self.window_ready = False

        self._load_embeddings()

    def _load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _init_insightface(self):
        # Initialize Shared InsightFace App
        runtime_mode = os.environ.get("INEFFA_RUNTIME_MODE", "").lower()
        use_gpu = self.config['system']['gpu_enabled'] and runtime_mode != "cpu"
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        logger.info(f"Initializing InsightFace with providers: {providers}")

        self.insightface_app = FaceAnalysis(
            name=self.config['detection']['model_name'], 
            allowed_modules=['detection', 'recognition'], 
            providers=providers
        )
        self.insightface_app.prepare(ctx_id=0, det_size=(self.config['detection']['input_size'], self.config['detection']['input_size']))

    def _load_embeddings(self):
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


    def run(self):
        self.stream.start()
        self._prepare_window()
        logger.info("System Started. Press 'q' to exit.")
        
        try:
            while True:
                frame = self.stream.read()
                if frame is None:
                    continue

                self._process_frame(frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stream.stop()
            cv2.destroyAllWindows()
            logger.info("System Stopped.")

    def _prepare_window(self):
        window_name = self.config['ui']['window_name']
        display_width = int(self.config['ui'].get('display_width', 960))
        display_height = int(self.config['ui'].get('display_height', 540))

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, display_width, display_height)
        self.window_ready = True

    def _resize_for_display(self, frame):
        display_width = int(self.config['ui'].get('display_width', 960))
        display_height = int(self.config['ui'].get('display_height', 540))
        if display_width <= 0 or display_height <= 0:
            return frame

        h, w = frame.shape[:2]
        scale = min(display_width / w, display_height / h, 1.0)
        if scale >= 1.0:
            return frame

        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

    def _process_frame(self, frame):
        # 0. Preprocessing (CLAHE)
        if self.config['input'].get('preprocessing', {}).get('enable_clahe', False):
            # Apply CLAHE to L channel of LAB color space
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(
                clipLimit=self.config['input']['preprocessing']['clahe_clip_limit'], 
                tileGridSize=(self.config['input']['preprocessing']['clahe_tile_grid_size'], 
                              self.config['input']['preprocessing']['clahe_tile_grid_size'])
            )
            cl = clahe.apply(l)
            
            limg = cv2.merge((cl, a, b))
            frame_processed = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        else:
            frame_processed = frame

        # 1. Detection (Use processed frame for better detection)
        faces = self.detector.detect(frame_processed)
        
        # 2. Tracking
        rects = [face.bbox.astype(int) for face in faces]
        objects = self.tracker.update(rects)
        
        # 3. Map tracker IDs to face objects
        faces_map = self._map_faces_to_tracker(objects, faces)
        
        # 4. Recognition Logic (Pass original frame for recognition/liveness to avoid artifacts?)
        # Actually, InsightFace often benefits from CLAHE too in bad lighting.
        # Let's use frame_processed for consistency.
        self._handle_recognition(frame_processed, faces_map)

        # 5. Display (Show original frame to user, but with overlays)
        # Or show processed? Usually users prefer seeing the enhanced version if it's dark.
        # Let's show the processed version if CLAHE is on, so they see what the AI sees.
        frame_display = frame_processed if self.config['input'].get('preprocessing', {}).get('enable_clahe', False) else frame
        
        frame_final = self.ui.draw_dashboard(
            frame_display,
            self.tracked_faces_state,
            faces_map,
            self.attendance_manager.get_recent_logs(),
            is_connected=True
        )
        frame_final = self._resize_for_display(frame_final)
        if not self.window_ready:
            self._prepare_window()
        cv2.imshow(self.config['ui']['window_name'], frame_final)

    def _map_faces_to_tracker(self, objects, faces):
        current_tracked_ids = set(objects.keys())
        faces_map = {} # {object_id: face_object}
        
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
        
        return faces_map

    def _handle_recognition(self, frame, faces_map):
        for object_id, face in faces_map.items():
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
            
            face_height = face.bbox[3] - face.bbox[1]
            
            # Retry if Unknown OR previously marked as SPOOF (to recover from false positives)
            if not state['processed'] or state['name'] in ["Unknown", "SPOOF"]:
                if face_height >= self.config['recognition']['min_face_size']:
                    
                    # Liveness Check
                    if self.config['liveness']['enabled']:
                        is_real, score = self.liveness_detector.check_liveness(frame, face.bbox)
                        if not is_real:
                            state['name'] = "SPOOF"
                            state['best_score'] = score
                            state['processed'] = True
                            return

                    # Extract Embedding
                    embedding = self.recognizer.get_embedding(frame, face)
                    if embedding is not None:
                        name, score = self._identify_face(embedding)
                        
                        if name != "Unknown":
                            state['name'] = name
                            state['best_score'] = score
                            state['processed'] = True
                            self.attendance_manager.log_attendance(name, frame, face.bbox)
                        else:
                            # Real but Unknown
                            state['name'] = "Unknown"
                            state['best_score'] = score

if __name__ == "__main__":
    system = AttendanceSystem()
    system.run()

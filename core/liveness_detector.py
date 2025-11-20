import cv2
import numpy as np
import onnxruntime
import logging

class LivenessDetector:
    def __init__(self, config):
        self.logger = logging.getLogger("LivenessDetector")
        self.config = config
        self.model_path = config['liveness']['model_path']
        self.threshold = config['liveness']['threshold']
        self.ort_session = None
        
        if config['liveness']['enabled']:
            self._load_model()

    def _load_model(self):
        try:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.config['system']['gpu_enabled'] else ['CPUExecutionProvider']
            self.ort_session = onnxruntime.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.ort_session.get_inputs()[0].name
            self.input_shape = self.ort_session.get_inputs()[0].shape
            self.logger.info(f"Liveness model loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Failed to load liveness model from {self.model_path}: {e}")
            self.logger.warning("Liveness detection will be disabled.")
            self.ort_session = None

    def check_liveness(self, frame, bbox):
        """
        Checks if the face in the bbox is real or spoof.
        Returns: (is_real: bool, score: float)
        """
        if self.ort_session is None:
            # If model failed to load or disabled, we can either fail open (True) or closed (False).
            # Failing open (True) is safer for usability if the feature is broken.
            return True, 1.0

        try:
            x1, y1, x2, y2 = map(int, bbox)
            h, w = frame.shape[:2]

            # Expand bbox slightly for context (MiniFASNet likes a bit of context)
            # Scale factor 2.7 is required for the 2.7_80x80 model
            scale = 2.7
            w_box = x2 - x1
            h_box = y2 - y1
            
            cx = x1 + w_box // 2
            cy = y1 + h_box // 2
            
            new_w = int(w_box * scale)
            new_h = int(h_box * scale)
            
            x1 = max(0, cx - new_w // 2)
            y1 = max(0, cy - new_h // 2)
            x2 = min(w, cx + new_w // 2)
            y2 = min(h, cy + new_h // 2)
            
            face_img = frame[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return False, 0.0

            # Resize to model input size (80x80 for MiniFASNetV2)
            target_size = (80, 80)
            img = cv2.resize(face_img, target_size)
            
            # Convert to float32
            img = img.astype(np.float32)
            
            # MiniFASNet expects HWC -> CHW
            img = img.transpose((2, 0, 1)) 
            img = np.expand_dims(img, axis=0) # Add batch dim
            
            # Run inference
            outputs = self.ort_session.run(None, {self.input_name: img})
            
            # Output is logits [batch, 3]
            # Class 0: Spoof, Class 1: Real, Class 2: Other/Mask
            logits = outputs[0][0]
            
            # Softmax
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / np.sum(exp_logits)
            
            real_score = probs[1]
            is_real = real_score > self.threshold
            
            # self.logger.info(f"Liveness Check: Score={real_score:.4f} | IsReal={is_real}")
            
            return is_real, real_score

        except Exception as e:
            self.logger.error(f"Error during liveness check: {e}")
            return True, 1.0 # Fail open on error

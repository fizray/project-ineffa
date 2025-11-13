"""
Face Detection and Alignment Component
Handles face detection, bounding box generation, and facial landmark alignment
"""

import cv2
import numpy as np
from facenet_pytorch import MTCNN
import os
from typing import List, Tuple, Optional, Dict, Any

class FaceDetector:
    def __init__(self, min_face_size: int = 40, detection_conf_threshold: float = 0.6):
        """
        Initialize face detector with MTCNN
        
        Args:
            min_face_size: Minimum face size to detect (pixels)
            detection_conf_threshold: Minimum confidence for detection
        """
        self.min_face_size = min_face_size
        self.detection_conf_threshold = detection_conf_threshold
        self.detector = MTCNN(keep_all=False, post_process=False, min_face_size=min_face_size)
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in a frame
        
        Args:
            frame: Input frame (BGR numpy array)
            
        Returns:
            List of detection results with keys:
            - bbox: (x, y, width, height)
            - confidence: detection confidence
            - landmarks: facial landmarks
        """
        # Convert BGR to RGB for MTCNN
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        orig_h, orig_w = frame.shape[:2]
        target_w = 480
        scale = target_w / float(orig_w) if orig_w > target_w else 1.0
        if scale != 1.0:
            small_rgb = cv2.resize(rgb_frame, (int(orig_w * scale), int(orig_h * scale)))
        else:
            small_rgb = rgb_frame
        boxes, probs, landmarks = self.detector.detect(small_rgb, landmarks=True)
        filtered_faces = []
        if boxes is None or probs is None:
            return filtered_faces
        for i, conf in enumerate(probs):
            if conf is None:
                continue
            if conf >= self.detection_conf_threshold:
                x1, y1, x2, y2 = boxes[i]
                x1 /= scale
                y1 /= scale
                x2 /= scale
                y2 /= scale
                w = int(x2 - x1)
                h = int(y2 - y1)
                x = int(x1)
                y = int(y1)
                lm = landmarks[i] if landmarks is not None else None
                lm_dict = None
                if lm is not None:
                    lm_dict = {
                        'left_eye': (int(lm[0][0] / scale), int(lm[0][1] / scale)),
                        'right_eye': (int(lm[1][0] / scale), int(lm[1][1] / scale)),
                        'nose': (int(lm[2][0] / scale), int(lm[2][1] / scale)),
                        'mouth_left': (int(lm[3][0] / scale), int(lm[3][1] / scale)),
                        'mouth_right': (int(lm[4][0] / scale), int(lm[4][1] / scale))
                    }
                filtered_faces.append({
                    'bbox': (x, y, w, h),
                    'confidence': float(conf),
                    'landmarks': lm_dict
                })
        
        return filtered_faces
    
    def align_face(self, frame: np.ndarray, landmarks: Dict[str, Tuple[int, int]]) -> Optional[np.ndarray]:
        """
        Align face based on facial landmarks
        
        Args:
            frame: Input frame
            landmarks: Facial landmarks dict with 'left_eye', 'right_eye', 'nose', 'mouth_left', 'mouth_right'
            
        Returns:
            Aligned face image or None if alignment fails
        """
        try:
            # Get eye coordinates
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            
            # Calculate angle for rotation
            dy = right_eye[1] - left_eye[1]
            dx = right_eye[0] - left_eye[0]
            angle = np.degrees(np.arctan2(dy, dx))
            
            # Get eye center
            eye_center = ((left_eye[0] + right_eye[0]) // 2, 
                         (left_eye[1] + right_eye[1]) // 2)
            
            # Get face center from bounding box
            # This requires bbox which should be passed separately
            # For now, use eye center as approximation
            
            # Calculate rotation matrix
            M = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
            
            # Apply rotation
            aligned_frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))
            
            return aligned_frame
            
        except Exception as e:
            print(f"Face alignment failed: {e}")
            return None
    
    def extract_face_roi(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], 
                        target_size: Tuple[int, int] = (160, 160)) -> Optional[np.ndarray]:
        """
        Extract and resize face ROI
        
        Args:
            frame: Input frame
            bbox: Bounding box (x, y, width, height)
            target_size: Target size for the face ROI
            
        Returns:
            Resized face ROI or None if extraction fails
        """
        try:
            x, y, w, h = bbox
            
            # Add padding to bbox
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(frame.shape[1] - x, w + 2 * padding)
            h = min(frame.shape[0] - y, h + 2 * padding)
            
            # Extract face ROI
            face_roi = frame[y:y+h, x:x+w]
            
            if face_roi.size == 0:
                return None
            
            # Resize to target size
            face_resized = cv2.resize(face_roi, target_size)
            
            return face_resized
            
        except Exception as e:
            print(f"Face ROI extraction failed: {e}")
            return None
    
    def process_frame(self, frame: np.ndarray, apply_alignment: bool = True) -> List[Dict[str, Any]]:
        """
        Process a frame to detect and optionally align faces
        
        Args:
            frame: Input frame
            apply_alignment: Whether to apply face alignment
            
        Returns:
            List of processed face data with aligned images
        """
        faces = self.detect_faces(frame)
        processed_faces = []
        
        for face_data in faces:
            try:
                bbox = face_data['bbox']
                landmarks = face_data['landmarks']
                
                # Extract face ROI
                face_roi = self.extract_face_roi(frame, bbox)
                if face_roi is None:
                    continue
                
                # Apply alignment if requested
                if apply_alignment:
                    aligned_frame = self.align_face(frame, landmarks)
                    if aligned_frame is not None:
                        aligned_roi = self.extract_face_roi(aligned_frame, bbox)
                        if aligned_roi is not None:
                            face_roi = aligned_roi
                
                processed_face = {
                    'bbox': bbox,
                    'confidence': face_data['confidence'],
                    'landmarks': landmarks,
                    'face_image': face_roi
                }
                
                processed_faces.append(processed_face)
                
            except Exception as e:
                print(f"Face processing failed: {e}")
                continue
        
        return processed_faces

# Test function
if __name__ == "__main__":
    # Create detector
    detector = FaceDetector(min_face_size=40, detection_conf_threshold=0.6)
    
    # Test with sample frame (you can modify this to test with real camera)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # This would normally be called with a real camera feed
    print("FaceDetector initialized and ready for use")
    print(f"Min face size: {detector.min_face_size}")
    print(f"Detection confidence threshold: {detector.detection_conf_threshold}")

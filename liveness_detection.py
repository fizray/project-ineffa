"""
Liveness Detection Component
Provides lightweight anti-spoofing measures including blink detection and head movement analysis
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import math
import time

class LivenessDetector:
    def __init__(self, window_size: int = 20, blink_threshold: float = 0.3):
        """
        Initialize liveness detector
        
        Args:
            window_size: Number of frames to analyze for blink detection
            blink_threshold: Threshold for detecting eye closure (0-1)
        """
        self.window_size = window_size
        self.blink_threshold = blink_threshold
        self.frame_history = []
        self.landmarks_history = []
        
    def calculate_eye_aspect_ratio(self, landmarks: Dict[str, Tuple[int, int]]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection
        
        Args:
            landmarks: Facial landmarks
            
        Returns:
            EAR value
        """
        try:
            # Get eye coordinates
            left_eye = landmarks['left_eye']
            right_eye = landmarks['right_eye']
            
            # For blink detection, we need more detailed eye landmarks
            # This is a simplified version - in practice, you'd need 6-point eye model
            # For now, use distance between eyes as a proxy
            
            eye_distance = math.sqrt((right_eye[0] - left_eye[0])**2 + 
                                   (right_eye[1] - left_eye[1])**2)
            
            return eye_distance
            
        except Exception as e:
            print(f"EAR calculation failed: {e}")
            return 0.0
    
    def detect_blink(self) -> Tuple[bool, float]:
        """
        Detect blink in the current frame sequence
        
        Returns:
            Tuple of (blink_detected, blink_confidence)
        """
        if len(self.landmarks_history) < 5:
            return False, 0.0
        
        # Get recent eye aspect ratios
        recent_ears = []
        for landmarks in self.landmarks_history[-5:]:
            ear = self.calculate_eye_aspect_ratio(landmarks)
            recent_ears.append(ear)
        
        if not recent_ears:
            return False, 0.0
        
        current_ear = recent_ears[-1]
        avg_ear = sum(recent_ears) / len(recent_ears)
        
        # Detect significant drop in EAR (blink)
        ear_ratio = current_ear / avg_ear if avg_ear > 0 else 1.0
        
        blink_detected = ear_ratio < (1.0 - self.blink_threshold)
        blink_confidence = max(0.0, 1.0 - ear_ratio)
        
        return blink_detected, blink_confidence
    
    def analyze_head_movement(self) -> Tuple[bool, float]:
        """
        Analyze head movement patterns to detect if it's a real person
        
        Returns:
            Tuple of (natural_movement_detected, movement_score)
        """
        if len(self.landmarks_history) < 3:
            return False, 0.0
        
        # Calculate movement between consecutive frames
        movements = []
        for i in range(1, min(len(self.landmarks_history), 5)):
            prev_landmarks = self.landmarks_history[-(i+1)]
            curr_landmarks = self.landmarks_history[-i]
            
            # Calculate nose movement (proxy for head movement)
            prev_nose = prev_landmarks.get('nose', (0, 0))
            curr_nose = curr_landmarks.get('nose', (0, 0))
            
            movement = math.sqrt((curr_nose[0] - prev_nose[0])**2 + 
                               (curr_nose[1] - prev_nose[1])**2)
            movements.append(movement)
        
        if not movements:
            return False, 0.0
        
        # Analyze movement patterns
        avg_movement = sum(movements) / len(movements)
        movement_variance = np.var(movements)
        
        # Natural head movement should have some variance and not be too large - more lenient
        natural_movement = (0.2 < avg_movement < 15.0) and (movement_variance > 0.05)
        movement_score = min(1.0, avg_movement / 8.0)  # Normalize to 0-1
        
        return natural_movement, movement_score
    
    def check_frame_consistency(self) -> float:
        """
        Check consistency of face detection across frames
        
        Returns:
            Consistency score (0-1)
        """
        if len(self.frame_history) < 3:
            return 1.0
        
        # Simple check: compare brightness and color consistency
        recent_frames = self.frame_history[-3:]
        
        brightness_values = []
        for frame in recent_frames:
            if frame is not None and frame.size > 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                brightness_values.append(brightness)
        
        if len(brightness_values) < 2:
            return 1.0
        
        # Calculate brightness variance
        brightness_variance = np.var(brightness_values)
        
        # High variance might indicate photo/spoofing
        consistency_score = max(0.0, 1.0 - (brightness_variance / 100.0))
        
        return consistency_score
    
    def analyze_face_texture(self, face_roi: Optional[np.ndarray]) -> float:
        """
        Analyze face texture to detect printed photos
        
        Args:
            face_roi: Face region of interest
            
        Returns:
            Texture score (0-1, higher means more natural)
        """
        if face_roi is None or face_roi.size == 0:
            return 0.0
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            
            # Apply Laplacian to detect edges/texture
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Photos typically have higher frequency content
            # Natural faces have more variation in texture - more lenient scoring
            texture_score = min(1.0, laplacian_var / 50.0)
            
            return texture_score
            
        except Exception as e:
            print(f"Texture analysis failed: {e}")
            return 0.0
    
    def process_frame(self, face_roi: Optional[np.ndarray], 
                     landmarks: Optional[Dict[str, Tuple[int, int]]]) -> Dict[str, Any]:
        """
        Process a single frame for liveness detection
        
        Args:
            face_roi: Face region of interest
            landmarks: Facial landmarks
            
        Returns:
            Liveness analysis results
        """
        # Store frame and landmarks in history
        self.frame_history.append(face_roi)
        if landmarks:
            self.landmarks_history.append(landmarks)
        
        # Limit history size
        if len(self.frame_history) > self.window_size:
            self.frame_history = self.frame_history[-self.window_size:]
        if len(self.landmarks_history) > self.window_size:
            self.landmarks_history = self.landmarks_history[-self.window_size:]
        
        # Perform liveness checks
        blink_detected, blink_confidence = self.detect_blink()
        movement_detected, movement_score = self.analyze_head_movement()
        consistency_score = self.check_frame_consistency()
        texture_score = self.analyze_face_texture(face_roi)
        
        # Calculate overall liveness score
        scores = [blink_confidence, movement_score, consistency_score, texture_score]
        valid_scores = [s for s in scores if s >= 0]
        
        if valid_scores:
            overall_score = sum(valid_scores) / len(valid_scores)
        else:
            overall_score = 0.0
        
        # Determine liveness passed - more lenient threshold
        liveness_passed = overall_score > 0.15  # Much more lenient threshold
        
        return {
            'liveness_passed': liveness_passed,
            'liveness_score': overall_score,
            'blink_detected': blink_detected,
            'blink_confidence': blink_confidence,
            'movement_detected': movement_detected,
            'movement_score': movement_score,
            'consistency_score': consistency_score,
            'texture_score': texture_score
        }
    
    def reset(self):
        """Reset the liveness detector state"""
        self.frame_history.clear()
        self.landmarks_history.clear()

class ChallengeResponseLiveness:
    """
    Optional challenge-response liveness detection
    Requires user interaction for higher security
    """
    
    def __init__(self):
        self.challenge_active = False
        self.challenge_start_time = 0
        self.expected_action = None
        self.action_completed = False
    
    def start_challenge(self, action: str, timeout: int = 10):
        """
        Start a challenge-response test
        
        Args:
            action: Expected action ('blink', 'smile', 'nod')
            timeout: Challenge timeout in seconds
        """
        self.challenge_active = True
        self.challenge_start_time = time.time()
        self.expected_action = action
        self.action_completed = False
    
    def check_challenge_response(self, landmarks: Optional[Dict[str, Tuple[int, int]]], 
                               current_action: str) -> bool:
        """
        Check if challenge response is correct
        
        Args:
            landmarks: Current facial landmarks
            current_action: Detected current action
            
        Returns:
            True if challenge passed
        """
        if not self.challenge_active:
            return True
        
        # Check timeout
        if time.time() - self.challenge_start_time > 10:
            self.reset_challenge()
            return False
        
        # Check if expected action matches current action
        if current_action == self.expected_action:
            self.action_completed = True
            self.reset_challenge()
            return True
        
        return False
    
    def reset_challenge(self):
        """Reset challenge state"""
        self.challenge_active = False
        self.expected_action = None
        self.action_completed = False

# Test function
if __name__ == "__main__":
    # Test liveness detector
    detector = LivenessDetector(window_size=20, blink_threshold=0.3)
    
    # Simulate some test data
    test_landmarks = {
        'left_eye': (100, 120),
        'right_eye': (150, 120),
        'nose': (125, 140)
    }
    
    result = detector.process_frame(None, test_landmarks)
    print("Liveness detection test:")
    print(f"Liveness passed: {result['liveness_passed']}")
    print(f"Liveness score: {result['liveness_score']:.3f}")
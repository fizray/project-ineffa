"""
Face Recognition Attendance PoC - Main Runner
Orchestrates the complete face recognition pipeline
"""

import cv2
import numpy as np
import time
import os
import sys
import yaml
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import all components
from face_detection import FaceDetector
from liveness_detection import LivenessDetector
from embedding_extractor import EmbeddingExtractor, EmbeddingManager
from matching_engine import MatchingEngine, EnrollmentMatcher
from logging_system import AttendanceLogger
from ui_system import UISystem, CameraInterface

class FaceAttendanceSystem:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the complete face attendance system
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self.load_config(config_path)
        self.is_running = False
        self.enrollment_mode = False
        self.current_user_id = None
        self.enrollment_images = []
        
        # Initialize components
        self.face_detector = None
        self.liveness_detector = None
        self.embedding_extractor = None
        self.embedding_manager = None
        self.matching_engine = None
        self.enrollment_matcher = None
        self.logger = None
        self.ui = None
        self.camera = None
        
        # Initialize cooldown from config
        self.attendance_cooldown = self.config.get('attendance_cooldown', 30)  # seconds between recordings per user
        
        # Attendance tracking - prevent multiple recordings
        self.last_attendance_time = {}  # user_id -> timestamp
        
        # Performance tracking
        self.processing_times = []
        self.frame_count = 0
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
            return self.get_default_config()
        except Exception as e:
            print(f"Failed to load config: {e}, using defaults")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'camera_id': 0,
            'frame_width': 640,
            'frame_height': 480,
            'grab_every_n_frames': 3,  # Process every 3rd frame for faster display
            'detection_conf_threshold': 0.6,
            'min_face_size': 40,
            'model_name': 'vgg_face2',
            'distance_metric': 'cosine',
            'threshold_match': 0.70,
            'save_snapshot_threshold': 0.75,
            'embeddings_path': 'embeddings.json',
            'log_path': 'attendance.csv',
            'snapshot_dir': 'snapshots',
            'attendance_cooldown': 30  # 30 seconds between attendance records per user
        }
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            print("Initializing system components...")
            
            # Initialize face detector
            self.face_detector = FaceDetector(
                min_face_size=self.config['min_face_size'],
                detection_conf_threshold=self.config['detection_conf_threshold']
            )
            
            # Initialize liveness detector
            self.liveness_detector = LivenessDetector(
                window_size=20, 
                blink_threshold=0.3
            )
            
            # Initialize embedding extractor with auto GPU detection
            self.embedding_extractor = EmbeddingExtractor(
                model_name=self.config['model_name'],
                config=self.config
            )
            
            # Print device info
            device_info = self.embedding_extractor.get_model_info()
            print(f"Embedding extractor device: {device_info['device']}")
            print(f"Model: {device_info['model_name']}")
            
            # Initialize embedding manager
            self.embedding_manager = EmbeddingManager(
                embeddings_file=self.config['embeddings_path']
            )
            
            # Initialize matching engine
            self.matching_engine = MatchingEngine(
                embedding_manager=self.embedding_manager,
                threshold_match=self.config['threshold_match'],
                distance_metric=self.config['distance_metric']
            )
            
            # Initialize enrollment matcher
            self.enrollment_matcher = EnrollmentMatcher(
                embedding_manager=self.embedding_manager,
                enrollment_threshold=0.75
            )
            
            # Initialize logger
            self.logger = AttendanceLogger(
                log_path=self.config['log_path'],
                snapshot_dir=self.config['snapshot_dir'],
                save_snapshot_threshold=self.config['save_snapshot_threshold']
            )
            
            # Initialize UI
            self.ui = UISystem(
                window_name="Face Attendance PoC",
                window_size=(self.config['frame_width'], self.config['frame_height'])
            )
            
            # Initialize camera
            self.camera = CameraInterface(
                camera_id=self.config['camera_id'],
                width=self.config['frame_width'],
                height=self.config['frame_height']
            )
            
            print("All components initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize components: {e}")
            raise
    
    def start(self):
        """Start the face attendance system"""
        try:
            print("Starting Face Attendance System...")
            
            # Initialize components
            self.initialize_components()
            
            # Start camera
            if not self.camera.start():
                print("Failed to start camera")
                return False
            
            # Start UI
            self.is_running = True
            self.ui.update_state(system_status="System Ready")
            
            print("System started successfully")
            print("Press 'H' for help, 'Q' to quit")
            
            # Start main loop
            self.run_main_loop()
            
            return True
            
        except Exception as e:
            print(f"Failed to start system: {e}")
            return False
    
    def run_main_loop(self):
        """Run the main processing loop"""
        frame_skip = self.config['grab_every_n_frames']
        frame_counter = 0
        latest_face_detections = []
        
        while self.is_running and self.ui.is_window_open():
            start_time = time.time()
            
            # Get frame from camera
            frame = self.camera.get_frame()
            if frame is None:
                continue
            
            frame_counter += 1
            
            # Process every N frames for performance
            if frame_counter % frame_skip == 0:
                # Process frame and get face detections for display
                latest_face_detections = self.process_frame_with_display(frame)
            
            # Calculate FPS
            processing_time = time.time() - start_time
            self.update_performance_stats(processing_time)
            
            # Show frame with face detection information
            self.ui.show_frame(frame, latest_face_detections)
            
            # Handle user input
            self.handle_user_input()
    
    def process_frame_with_display(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Process a single frame and return face detection info for display
        
        Args:
            frame: Input frame
            
        Returns:
            List of face detection results for display
        """
        try:
            # Detect faces
            face_detections = self.face_detector.process_frame(frame, apply_alignment=True)
            
            # Prepare display data for all detected faces
            display_faces = []
            
            if not face_detections:
                # No faces detected
                self.ui.update_state(
                    system_status="No face detected",
                    face_count=0,
                    processing_fps=self.get_current_fps()
                )
                return display_faces
            
            # Process each detected face
            for i, detection in enumerate(face_detections):
                face_roi = detection['face_image']
                landmarks = detection['landmarks']
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # Create display info for this face
                face_display_info = {
                    'bbox': bbox,
                    'confidence': confidence,
                    'user_name': "Unknown",
                    'match_score': 0.0,
                    'is_matched': False,
                    'liveness_score': 0.0,
                    'liveness_passed': False
                }
                
                # Only process the first (largest) face for recognition
                if i == 0:
                    # Liveness detection
                    liveness_result = self.liveness_detector.process_frame(face_roi, landmarks)
                    face_display_info['liveness_score'] = liveness_result.get('liveness_score', 0.0)
                    face_display_info['liveness_passed'] = liveness_result.get('liveness_passed', False)
                    
                    # Only proceed with recognition if liveness passed
                    if liveness_result.get('liveness_passed', False):
                        # Extract embedding
                        embedding = self.embedding_extractor.extract_embedding(face_roi)
                        if embedding is not None:
                            # Match against gallery
                            match_result = self.matching_engine.match_single_embedding(embedding)
                            
                            # Update display info with recognition results
                            face_display_info['user_name'] = match_result.user_name if match_result.is_match else "Unknown"
                            face_display_info['match_score'] = match_result.match_score
                            face_display_info['is_matched'] = match_result.is_match
                            
                            # Log attendance if matched
                            if match_result.is_match:
                                self.log_attendance(frame, match_result, liveness_result, confidence)
                            
                            # Handle enrollment mode
                            if self.enrollment_mode:
                                self.handle_enrollment(embedding, face_roi)
                        
                        # Update UI state with recognition results
                        self.ui.update_state(
                            match_result=match_result if i == 0 else None,
                            liveness_result=liveness_result,
                            face_count=len(face_detections),
                            processing_fps=self.get_current_fps()
                        )
                    else:
                        # Liveness failed
                        self.ui.update_state(
                            system_status="Liveness check failed",
                            face_count=len(face_detections),
                            liveness_result=liveness_result,
                            processing_fps=self.get_current_fps()
                        )
                else:
                    # For additional faces, just update face count
                    pass
                
                display_faces.append(face_display_info)
            
            return display_faces
            
        except Exception as e:
            print(f"Frame processing error: {e}")
            self.ui.update_state(system_status="Processing error")
            return []
    
    def process_frame(self, frame: np.ndarray):
        """Legacy method for backward compatibility"""
        # This method is kept for compatibility but delegates to process_frame_with_display
        self.process_frame_with_display(frame)
    
    def log_attendance(self, frame: np.ndarray, match_result, liveness_result: Dict[str, Any],
                      detection_confidence: float):
        """Log attendance record with cooldown to prevent multiple recordings"""
        try:
            current_time = time.time()
            user_id = match_result.user_id
            
            # Check if user has recently been recorded
            if user_id in self.last_attendance_time:
                time_since_last = current_time - self.last_attendance_time[user_id]
                if time_since_last < self.attendance_cooldown:
                    # Still within cooldown period, don't record again
                    self.ui.update_state(
                        system_status=f"Already recorded ({int(self.attendance_cooldown - time_since_last)}s ago)"
                    )
                    return
            
            # Record the attendance
            processing_time = self.get_average_processing_time()
            
            self.logger.log_attendance_with_frame(
                frame=frame,
                user_id=user_id,
                user_name=match_result.user_name,
                matched_score=match_result.match_score,
                liveness_passed=liveness_result['liveness_passed'],
                note="auto",
                face_detected=True,
                detection_confidence=detection_confidence,
                processing_time_ms=processing_time * 1000
            )
            
            # Update last attendance time
            self.last_attendance_time[user_id] = current_time
            
            # Update status
            self.ui.update_state(
                system_status=f"Attendance recorded for {match_result.user_name}"
            )
            
        except Exception as e:
            print(f"Failed to log attendance: {e}")
    
    def handle_enrollment(self, embedding: np.ndarray, face_roi: np.ndarray):
        """Handle enrollment process"""
        if self.current_user_id is None:
            # Start new enrollment - prompt for user info
            # In a real system, this would be interactive
            self.current_user_id = f"user_{int(time.time())}"
            self.enrollment_images = []
            self.ui.update_state(system_status=f"Enrolling {self.current_user_id}")
        
        # Add current embedding to enrollment
        self.enrollment_images.append(embedding)
        
        # Save snapshot
        timestamp = datetime.now().isoformat()
        snapshot_path = os.path.join(self.config['snapshot_dir'], 
                                   f"enroll_{self.current_user_id}_{len(self.enrollment_images)}.jpg")
        cv2.imwrite(snapshot_path, face_roi)
        
        # Check if we have enough images
        if len(self.enrollment_images) >= 10:  # Require 10 images
            # Verify enrollment quality
            quality = self.enrollment_matcher.verify_enrollment_quality(self.enrollment_images)
            
            if quality['quality'] in ['good', 'excellent']:
                # Save embeddings
                user_name = f"User_{self.current_user_id}"  # Placeholder
                self.embedding_manager.add_user_embeddings(
                    user_id=self.current_user_id,
                    user_name=user_name,
                    embeddings=self.enrollment_images,
                    metadata={"enrollment_quality": quality['quality']}
                )
                
                print(f"Successfully enrolled {self.current_user_id} with {len(self.enrollment_images)} images")
                
            else:
                print(f"Enrollment quality poor: {quality['quality']}")
            
            # Reset enrollment
            self.reset_enrollment()
    
    def reset_enrollment(self):
        """Reset enrollment state"""
        self.enrollment_mode = False
        self.current_user_id = None
        self.enrollment_images = []
        self.liveness_detector.reset()
        self.ui.update_state(system_status="Enrollment complete")
    
    def handle_user_input(self):
        """Handle keyboard input from UI"""
        key = self.ui.wait_for_key(1)  # 1ms timeout
        
        if key:
            action = self.ui.handle_key_input(key)
            
            if action['action'] == 'quit':
                self.stop()
            elif action['action'] == 'enroll':
                if not self.enrollment_mode:
                    self.start_enrollment()
            elif action['action'] == 'help':
                self.ui.show_help()
            elif action['action'] == 'save_snapshot':
                self.save_manual_snapshot()
            elif action['action'] == 'reset':
                self.reset_detection()
            elif action['action'] == 'reset_attendance':
                self.reset_attendance_tracking()
    
    def start_enrollment(self):
        """Start enrollment mode"""
        self.enrollment_mode = True
        self.current_user_id = None
        self.enrollment_images = []
        self.liveness_detector.reset()
        self.ui.update_state(enrollment_mode=True, system_status="Starting enrollment...")
    
    def save_manual_snapshot(self):
        """Save manual snapshot"""
        frame = self.camera.get_frame()
        if frame is not None:
            timestamp = datetime.now().isoformat()
            snapshot_path = os.path.join(self.config['snapshot_dir'], 
                                       f"manual_{timestamp.replace(':', '-')}.jpg")
            cv2.imwrite(snapshot_path, frame)
            print(f"Manual snapshot saved: {snapshot_path}")
    
    def reset_detection(self):
        """Reset detection state"""
        self.liveness_detector.reset()
        self.ui.update_state(system_status="Detection reset")
    
    def reset_attendance_tracking(self):
        """Reset attendance cooldown tracking"""
        self.last_attendance_time.clear()
        self.ui.update_state(system_status="Attendance tracking reset")
        print("Attendance cooldown tracking reset - users can be recorded again")
    
    def update_performance_stats(self, processing_time: float):
        """Update performance statistics"""
        self.processing_times.append(processing_time)
        
        # Keep only recent times
        if len(self.processing_times) > 30:
            self.processing_times = self.processing_times[-30:]
        
        self.frame_count += 1
    
    def get_current_fps(self) -> float:
        """Get current processing FPS"""
        if not self.processing_times:
            return 0.0
        return 1.0 / np.mean(self.processing_times)
    
    def get_average_processing_time(self) -> float:
        """Get average processing time"""
        if not self.processing_times:
            return 0.0
        return np.mean(self.processing_times)
    
    def stop(self):
        """Stop the system"""
        print("Stopping system...")
        self.is_running = False
        
        # Cleanup components
        if self.camera:
            self.camera.stop()
        if self.ui:
            self.ui.cleanup()
        
        print("System stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "is_running": self.is_running,
            "enrollment_mode": self.enrollment_mode,
            "enrolled_users": len(self.embedding_manager.list_users()),
            "processing_fps": self.get_current_fps(),
            "avg_processing_time": self.get_average_processing_time(),
            "frame_count": self.frame_count,
            "current_config": self.config
        }

def main():
    """Main entry point"""
    print("Face Recognition Attendance PoC")
    print("=" * 40)
    
    # Check for config file
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Create and start system
    system = FaceAttendanceSystem(config_path)
    
    try:
        success = system.start()
        if success:
            print("System running successfully")
        else:
            print("System failed to start")
            return 1
    except KeyboardInterrupt:
        print("\\nSystem interrupted by user")
    except Exception as e:
        print(f"System error: {e}")
        return 1
    finally:
        system.stop()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
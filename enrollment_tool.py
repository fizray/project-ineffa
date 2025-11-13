"""
Enrollment Tool for Face Recognition Attendance PoC
Provides utilities for enrolling new users and managing the gallery
"""

import os
import cv2
import numpy as np
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
import argparse

from face_detection import FaceDetector
from liveness_detection import LivenessDetector
from embedding_extractor import EmbeddingExtractor, EmbeddingManager
from matching_engine import EnrollmentMatcher

class EnrollmentTool:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize enrollment tool
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self.load_config(config_path)
        self.face_detector = None
        self.liveness_detector = None
        self.embedding_extractor = None
        self.embedding_manager = None
        self.enrollment_matcher = None
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'camera_id': 0,
            'frame_width': 640,
            'frame_height': 480,
            'min_face_size': 40,
            'detection_conf_threshold': 0.6,
            'model_name': 'vgg_face2',
            'embeddings_path': 'embeddings.json',
            'gallery_dir': 'gallery',
            'enrollment_threshold': 0.75
        }
    
    def initialize_components(self):
        """Initialize all required components"""
        try:
            print("Initializing enrollment components...")
            
            self.face_detector = FaceDetector(
                min_face_size=self.config['min_face_size'],
                detection_conf_threshold=self.config['detection_conf_threshold']
            )
            
            self.liveness_detector = LivenessDetector(
                window_size=20,
                blink_threshold=0.3
            )
            
            self.embedding_extractor = EmbeddingExtractor(
                model_name=self.config['model_name']
            )
            
            self.embedding_manager = EmbeddingManager(
                embeddings_file=self.config['embeddings_path']
            )
            
            self.enrollment_matcher = EnrollmentMatcher(
                embedding_manager=self.embedding_manager,
                enrollment_threshold=self.config['enrollment_threshold']
            )
            
            print("Components initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize components: {e}")
            raise
    
    def setup_camera(self) -> Optional[cv2.VideoCapture]:
        """Setup and return camera capture"""
        try:
            cap = cv2.VideoCapture(self.config['camera_id'])
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['frame_width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['frame_height'])
            
            if not cap.isOpened():
                print("Failed to open camera")
                return None
            
            print("Camera initialized successfully")
            return cap
            
        except Exception as e:
            print(f"Failed to setup camera: {e}")
            return None
    
    def create_user_gallery(self, user_id: str) -> str:
        """Create user gallery directory"""
        gallery_dir = self.config['gallery_dir']
        user_gallery = os.path.join(gallery_dir, user_id)
        
        os.makedirs(user_gallery, exist_ok=True)
        return user_gallery
    
    def capture_enrollment_images(self, cap: cv2.VideoCapture, user_id: str, 
                                num_images: int = 20) -> List[str]:
        """
        Capture images for enrollment
        
        Args:
            cap: Camera capture object
            user_id: User identifier
            num_images: Number of images to capture
            
        Returns:
            List of captured image paths
        """
        captured_images = []
        user_gallery = self.create_user_gallery(user_id)
        
        print(f"Starting enrollment for user: {user_id}")
        print(f"Will capture {num_images} images")
        print("Please look at the camera and vary your position slightly")
        print("Press 'c' to capture, 'q' to quit, 'r' to reset")
        
        frame_count = 0
        
        while len(captured_images) < num_images and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces
            detections = self.face_detector.process_frame(frame, apply_alignment=True)
            
            # Draw status on frame
            display_frame = frame.copy()
            if detections:
                detection = detections[0]  # Use largest face
                bbox = detection['bbox']
                confidence = detection['confidence']
                
                # Draw bounding box
                x, y, w, h = bbox
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Show progress
                cv2.putText(display_frame, f"Face detected! ({len(captured_images)}/{num_images})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, "No face detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.putText(display_frame, f"User: {user_id}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.putText(display_frame, "Press 'c' to capture, 'q' to quit", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow("Enrollment", display_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('c') and detections:
                # Capture image
                image_path = os.path.join(user_gallery, f"img_{len(captured_images):03d}.jpg")
                cv2.imwrite(image_path, frame)
                captured_images.append(image_path)
                print(f"Captured image {len(captured_images)}/{num_images}")
                
                # Add some delay
                cv2.waitKey(500)
            
            frame_count += 1
        
        cv2.destroyAllWindows()
        return captured_images
    
    def enroll_user_from_images(self, user_id: str, user_name: str, 
                              image_paths: List[str]) -> Dict[str, Any]:
        """
        Enroll user from pre-captured images
        
        Args:
            user_id: User identifier
            user_name: User display name
            image_paths: List of image file paths
            
        Returns:
            Enrollment result dictionary
        """
        try:
            print(f"Processing {len(image_paths)} images for user {user_id}...")
            
            # Extract embeddings from all images
            valid_embeddings = []
            failed_images = []
            
            for i, image_path in enumerate(image_paths):
                try:
                    # Load image
                    image = cv2.imread(image_path)
                    if image is None:
                        failed_images.append(image_path)
                        continue
                    
                    # Detect and extract face
                    detections = self.face_detector.process_frame(image, apply_alignment=True)
                    if not detections:
                        failed_images.append(image_path)
                        continue
                    
                    face_roi = detections[0]['face_image']
                    
                    # Extract embedding
                    embedding = self.embedding_extractor.extract_embedding(face_roi)
                    if embedding is not None:
                        valid_embeddings.append(embedding)
                        print(f"Processed image {i+1}/{len(image_paths)}")
                    else:
                        failed_images.append(image_path)
                        
                except Exception as e:
                    print(f"Failed to process {image_path}: {e}")
                    failed_images.append(image_path)
            
            if len(valid_embeddings) < 3:
                return {
                    "success": False,
                    "error": f"Only {len(valid_embeddings)} valid embeddings extracted. Need at least 3.",
                    "valid_embeddings": len(valid_embeddings),
                    "failed_images": len(failed_images)
                }
            
            # Check for duplicates
            duplicate_user = None
            for embedding in valid_embeddings[:1]:  # Check first embedding
                duplicate = self.enrollment_matcher.find_duplicate_user(embedding)
                if duplicate:
                    duplicate_user = duplicate
                    break
            
            if duplicate_user:
                return {
                    "success": False,
                    "error": f"Face matches existing user: {duplicate_user}",
                    "duplicate_user": duplicate_user
                }
            
            # Verify enrollment quality
            quality_result = self.enrollment_matcher.verify_enrollment_quality(valid_embeddings)
            
            if quality_result['quality'] in ['poor']:
                return {
                    "success": False,
                    "error": f"Enrollment quality too poor: {quality_result['quality']}",
                    "quality": quality_result
                }
            
            # Save embeddings
            metadata = {
                "enrolled_at": datetime.now().isoformat(),
                "num_images": len(image_paths),
                "valid_embeddings": len(valid_embeddings),
                "quality": quality_result['quality'],
                "enrollment_method": "batch_images"
            }
            
            self.embedding_manager.add_user_embeddings(
                user_id=user_id,
                user_name=user_name,
                embeddings=valid_embeddings,
                metadata=metadata
            )
            
            return {
                "success": True,
                "user_id": user_id,
                "user_name": user_name,
                "valid_embeddings": len(valid_embeddings),
                "failed_images": len(failed_images),
                "quality": quality_result,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Enrollment failed: {str(e)}"
            }
    
    def enroll_user_realtime(self, user_id: str, user_name: str, 
                           num_images: int = 20) -> Dict[str, Any]:
        """
        Enroll user with real-time capture
        
        Args:
            user_id: User identifier
            user_name: User display name
            num_images: Number of images to capture
            
        Returns:
            Enrollment result dictionary
        """
        try:
            self.initialize_components()
            
            # Setup camera
            cap = self.setup_camera()
            if cap is None:
                return {"success": False, "error": "Failed to setup camera"}
            
            # Capture images
            image_paths = self.capture_enrollment_images(cap, user_id, num_images)
            cap.release()
            
            if not image_paths:
                return {"success": False, "error": "No images captured"}
            
            # Process captured images
            result = self.enroll_user_from_images(user_id, user_name, image_paths)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": f"Real-time enrollment failed: {str(e)}"}
    
    def list_enrolled_users(self) -> List[Dict[str, Any]]:
        """List all enrolled users"""
        users = []
        for user_id, user_data in self.embedding_manager.embeddings.items():
            users.append({
                "user_id": user_id,
                "name": user_data["name"],
                "num_embeddings": len(user_data["embeddings"]),
                "enrolled_at": user_data.get("metadata", {}).get("enrolled_at", "Unknown"),
                "quality": user_data.get("metadata", {}).get("quality", "Unknown")
            })
        return users
    
    def remove_user(self, user_id: str) -> bool:
        """Remove user from enrollment"""
        try:
            # Remove from embeddings
            success = self.embedding_manager.remove_user(user_id)
            
            # Remove from gallery
            user_gallery = os.path.join(self.config['gallery_dir'], user_id)
            if os.path.exists(user_gallery):
                import shutil
                shutil.rmtree(user_gallery)
            
            return success
        except Exception as e:
            print(f"Failed to remove user {user_id}: {e}")
            return False
    
    def export_users(self, output_path: str) -> bool:
        """Export user data to JSON file"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_users": len(self.embedding_manager.embeddings),
                "users": {}
            }
            
            for user_id, user_data in self.embedding_manager.embeddings.items():
                export_data["users"][user_id] = {
                    "name": user_data["name"],
                    "embeddings": user_data["embeddings"],
                    "metadata": user_data.get("metadata", {})
                }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Exported {export_data['total_users']} users to {output_path}")
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False

def main():
    """Main enrollment tool"""
    parser = argparse.ArgumentParser(description="Face Recognition Enrollment Tool")
    parser.add_argument('--mode', choices=['realtime', 'batch', 'list', 'remove', 'export'], 
                       default='realtime', help='Enrollment mode')
    parser.add_argument('--user-id', help='User ID')
    parser.add_argument('--user-name', help='User name')
    parser.add_argument('--num-images', type=int, default=20, help='Number of images to capture')
    parser.add_argument('--image-dir', help='Directory with enrollment images')
    parser.add_argument('--output', help='Output path for export')
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = EnrollmentTool()
    
    if args.mode == 'realtime':
        if not args.user_id or not args.user_name:
            print("Error: --user-id and --user-name required for realtime mode")
            return 1
        
        result = tool.enroll_user_realtime(args.user_id, args.user_name, args.num_images)
        print(f"Enrollment result: {result}")
        
    elif args.mode == 'batch':
        if not args.user_id or not args.user_name or not args.image_dir:
            print("Error: --user-id, --user-name, and --image-dir required for batch mode")
            return 1
        
        # Get all images from directory
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_paths = []
        for ext in image_extensions:
            image_paths.extend([os.path.join(args.image_dir, f) for f in os.listdir(args.image_dir) 
                              if f.lower().endswith(ext)])
        
        result = tool.enroll_user_from_images(args.user_id, args.user_name, image_paths)
        print(f"Enrollment result: {result}")
        
    elif args.mode == 'list':
        users = tool.list_enrolled_users()
        print(f"Enrolled users ({len(users)}):")
        for user in users:
            print(f"  {user['user_id']}: {user['name']} ({user['num_embeddings']} embeddings)")
            
    elif args.mode == 'remove':
        if not args.user_id:
            print("Error: --user-id required for remove mode")
            return 1
        
        success = tool.remove_user(args.user_id)
        print(f"Remove user {args.user_id}: {'Success' if success else 'Failed'}")
        
    elif args.mode == 'export':
        output_path = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        success = tool.export_users(output_path)
        print(f"Export: {'Success' if success else 'Failed'}")
    
    return 0

if __name__ == "__main__":
    exit(main())
"""
UI System Component
Provides real-time feedback using OpenCV window with overlay information
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import time
from dataclasses import dataclass
from matching_engine import MatchResult

@dataclass
class UIState:
    """UI state information"""
    current_user: str
    match_score: float
    liveness_score: float
    is_matched: bool
    liveness_passed: bool
    enrollment_mode: bool
    processing_fps: float
    face_count: int
    system_status: str

class UISystem:
    def __init__(self, window_name: str = "Face Attendance PoC", 
                 window_size: Tuple[int, int] = (1280, 720)):
        """
        Initialize UI system
        
        Args:
            window_name: Name of the display window
            window_size: Size of the display window
        """
        self.window_name = window_name
        self.window_width, self.window_height = window_size
        self.state = UIState(
            current_user="",
            match_score=0.0,
            liveness_score=0.0,
            is_matched=False,
            liveness_passed=False,
            enrollment_mode=False,
            processing_fps=0.0,
            face_count=0,
            system_status="Ready"
        )
        
        # UI colors
        self.colors = {
            'bg': (0, 0, 0),
            'text': (255, 255, 255),
            'success': (0, 255, 0),
            'warning': (0, 255, 255),
            'error': (0, 0, 255),
            'unknown': (128, 128, 128),
            'enrollment': (255, 165, 0)
        }
        
        # Font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        
        # Initialize window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)
    
    def update_state(self, match_result: Optional[MatchResult] = None,
                    liveness_result: Optional[Dict[str, Any]] = None,
                    enrollment_mode: bool = False,
                    processing_fps: float = 0.0,
                    face_count: int = 0,
                    system_status: str = ""):
        """
        Update UI state
        
        Args:
            match_result: Current match result
            liveness_result: Current liveness result
            enrollment_mode: Whether in enrollment mode
            processing_fps: Current processing FPS
            face_count: Number of faces detected
            system_status: System status message
        """
        if match_result:
            self.state.current_user = match_result.user_name
            self.state.match_score = match_result.match_score
            self.state.is_matched = match_result.is_match
        
        if liveness_result:
            self.state.liveness_score = liveness_result.get('liveness_score', 0.0)
            self.state.liveness_passed = liveness_result.get('liveness_passed', False)
        
        self.state.enrollment_mode = enrollment_mode
        self.state.processing_fps = processing_fps
        self.state.face_count = face_count
        if system_status:
            self.state.system_status = system_status
    
    def draw_text_with_background(self, img: np.ndarray, text: str, position: Tuple[int, int],
                                color: Tuple[int, int, int], background_color: Tuple[int, int, int],
                                font_scale: float = None, thickness: int = None):
        """
        Draw text with background rectangle
        
        Args:
            img: Image to draw on
            text: Text to draw
            position: Top-left position (x, y)
            color: Text color
            background_color: Background rectangle color
            font_scale: Font scale
            thickness: Font thickness
        """
        font_scale = font_scale or self.font_scale
        thickness = thickness or self.font_thickness
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(text, self.font, font_scale, thickness)
        
        # Draw background rectangle
        cv2.rectangle(img, 
                     (position[0], position[1] - text_height - baseline),
                     (position[0] + text_width, position[1] + baseline),
                     background_color, -1)
        
        # Draw text
        cv2.putText(img, text, position, self.font, font_scale, color, thickness)
    
    def draw_status_panel(self, img: np.ndarray):
        """Draw status information panel"""
        panel_x = 10
        panel_y = 10
        panel_width = 300
        panel_height = 200
        
        # Draw panel background
        cv2.rectangle(img, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     self.colors['bg'], -1)
        
        # Draw panel border
        cv2.rectangle(img, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     self.colors['text'], 2)
        
        y_offset = panel_y + 30
        
        # Title
        self.draw_text_with_background(img, "FACE ATTENDANCE PoC", 
                                     (panel_x + 10, y_offset),
                                     self.colors['text'], self.colors['bg'],
                                     font_scale=0.7, thickness=2)
        y_offset += 40
        
        # Current user
        user_text = f"User: {self.state.current_user or 'Unknown'}"
        user_color = self.colors['success'] if self.state.is_matched else self.colors['unknown']
        self.draw_text_with_background(img, user_text, (panel_x + 10, y_offset), 
                                     user_color, self.colors['bg'])
        y_offset += 25
        
        # Match score
        score_text = f"Score: {self.state.match_score:.3f}"
        score_color = self.colors['success'] if self.state.is_matched else self.colors['error']
        self.draw_text_with_background(img, score_text, (panel_x + 10, y_offset),
                                     score_color, self.colors['bg'])
        y_offset += 25
        
        # Liveness status
        liveness_text = f"Liveness: {'PASS' if self.state.liveness_passed else 'FAIL'}"
        liveness_color = self.colors['success'] if self.state.liveness_passed else self.colors['error']
        self.draw_text_with_background(img, liveness_text, (panel_x + 10, y_offset),
                                     liveness_color, self.colors['bg'])
        y_offset += 25
        
        # System status
        status_text = f"Status: {self.state.system_status}"
        self.draw_text_with_background(img, status_text, (panel_x + 10, y_offset),
                                     self.colors['warning'], self.colors['bg'])
        y_offset += 25
        
        # Performance info
        perf_text = f"FPS: {self.state.processing_fps:.1f} | Faces: {self.state.face_count}"
        self.draw_text_with_background(img, perf_text, (panel_x + 10, y_offset),
                                     self.colors['text'], self.colors['bg'],
                                     font_scale=0.5)
    
    def draw_enrollment_panel(self, img: np.ndarray):
        """Draw enrollment mode information"""
        if not self.state.enrollment_mode:
            return
        
        panel_x = self.window_width - 320
        panel_y = 10
        panel_width = 310
        panel_height = 150
        
        # Draw enrollment panel
        cv2.rectangle(img, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     self.colors['enrollment'], -1)
        
        # Draw border
        cv2.rectangle(img, (panel_x, panel_y), 
                     (panel_x + panel_width, panel_y + panel_height),
                     self.colors['text'], 2)
        
        y_offset = panel_y + 30
        
        # Title
        self.draw_text_with_background(img, "ENROLLMENT MODE", 
                                     (panel_x + 10, y_offset),
                                     self.colors['bg'], self.colors['enrollment'],
                                     font_scale=0.7, thickness=2)
        y_offset += 40
        
        # Instructions
        instructions = [
            "Press 'E' to enroll new user",
            "Press 'Q' to quit",
            "Press 'S' to save snapshot"
        ]
        
        for instruction in instructions:
            self.draw_text_with_background(img, instruction, (panel_x + 10, y_offset),
                                         self.colors['bg'], self.colors['enrollment'],
                                         font_scale=0.5)
            y_offset += 20
    
    def draw_face_info(self, img: np.ndarray, bbox: Tuple[int, int, int, int],
                      user_name: str, match_score: float, is_matched: bool,
                      liveness_score: float = 0.0, liveness_passed: bool = False):
        """
        Draw face bounding box and comprehensive information
        
        Args:
            img: Image to draw on
            bbox: Bounding box (x, y, w, h)
            user_name: User name or "Unknown"
            match_score: Match confidence score
            is_matched: Whether face is matched
            liveness_score: Liveness detection score
            liveness_passed: Whether liveness check passed
        """
        x, y, w, h = bbox
        
        # Choose color based on match status and liveness
        if is_matched and liveness_passed:
            color = self.colors['success']  # Green for matched + live
        elif liveness_passed:
            color = self.colors['warning']  # Yellow for live but unknown
        else:
            color = self.colors['error']    # Red for not live
        
        # Draw bounding box
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
        
        # Draw label background
        label_y = y - 15
        if label_y < 0:
            label_y = y + h + 25
        
        # Create comprehensive label text
        status_text = "LIVE" if liveness_passed else "FAKE"
        if is_matched:
            label_text = f"{user_name} | {match_score:.2f} | {status_text}"
        else:
            label_text = f"Unknown | {match_score:.2f} | {status_text}"
        
        # Draw label with background
        self.draw_text_with_background(img, label_text, (x, label_y),
                                     color, self.colors['bg'], font_scale=0.5)
        
        # Draw match score bar below the main label
        if match_score > 0:
            self.draw_score_bar(img, (x, label_y + 20), match_score, is_matched)
        
        # Draw liveness indicator
        if liveness_score > 0:
            self.draw_small_liveness_indicator(img, (x + w + 5, y + 5), liveness_score, liveness_passed)
    
    def draw_score_bar(self, img: np.ndarray, position: Tuple[int, int], score: float, is_matched: bool):
        """Draw a small score bar"""
        x, y = position
        bar_width = 80
        bar_height = 6
        
        # Background
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), self.colors['bg'], -1)
        
        # Fill based on score
        fill_width = int(bar_width * score)
        bar_color = self.colors['success'] if is_matched else self.colors['error']
        cv2.rectangle(img, (x, y), (x + fill_width, y + bar_height), bar_color, -1)
        
        # Border
        cv2.rectangle(img, (x, y), (x + bar_width, y + bar_height), self.colors['text'], 1)
    
    def draw_small_liveness_indicator(self, img: np.ndarray, position: Tuple[int, int],
                                    liveness_score: float, liveness_passed: bool):
        """Draw a small liveness indicator"""
        x, y = position
        size = 15
        
        # Draw circle
        color = self.colors['success'] if liveness_passed else self.colors['error']
        cv2.circle(img, (x + size//2, y + size//2), size//2, color, -1)
        cv2.circle(img, (x + size//2, y + size//2), size//2, self.colors['text'], 1)
        
        # Draw check mark or X
        if liveness_passed:
            # Check mark
            cv2.line(img, (x + 3, y + size//2), (x + size//2, y + size - 3), self.colors['text'], 2)
            cv2.line(img, (x + size//2, y + size - 3), (x + size - 3, y + 3), self.colors['text'], 2)
        else:
            # X mark
            cv2.line(img, (x + 3, y + 3), (x + size - 3, y + size - 3), self.colors['text'], 2)
            cv2.line(img, (x + size - 3, y + 3), (x + 3, y + size - 3), self.colors['text'], 2)
    
    def draw_liveness_indicator(self, img: np.ndarray, bbox: Tuple[int, int, int, int],
                               liveness_score: float, liveness_passed: bool):
        """
        Draw liveness indicator
        
        Args:
            img: Image to draw on
            bbox: Face bounding box
            liveness_score: Liveness score (0-1)
            liveness_passed: Whether liveness check passed
        """
        x, y, w, h = bbox
        
        # Draw liveness bar
        bar_width = 60
        bar_height = 8
        bar_x = x + w + 5
        bar_y = y + h - 20
        
        # Background bar
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     self.colors['bg'], -1)
        
        # Foreground bar based on score
        fill_width = int(bar_width * liveness_score)
        bar_color = self.colors['success'] if liveness_passed else self.colors['error']
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height),
                     bar_color, -1)
        
        # Border
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                     self.colors['text'], 1)
    
    def show_frame(self, frame: np.ndarray, face_detections: List[Dict[str, Any]] = None):
        """
        Display frame with all UI elements including user names on bounding boxes
        
        Args:
            frame: Frame to display
            face_detections: List of face detection results with user information
        """
        if frame is None:
            return
        
        # Resize frame to fit window
        display_frame = cv2.resize(frame, (self.window_width, self.window_height))
        
        # Draw status panels
        self.draw_status_panel(display_frame)
        self.draw_enrollment_panel(display_frame)
        
        # Draw face information if detections provided
        if face_detections:
            for detection in face_detections:
                bbox = detection.get('bbox', (0, 0, 0, 0))
                
                # Use the user information from the detection data
                user_name = detection.get('user_name', 'Unknown')
                confidence = detection.get('match_score', 0.0)
                is_matched = detection.get('is_matched', False)
                liveness_score = detection.get('liveness_score', 0.0)
                liveness_passed = detection.get('liveness_passed', False)
                
                # Draw face bounding box with user name
                self.draw_face_info(display_frame, bbox, user_name, confidence, is_matched)
                
                # Draw liveness indicator for this face
                if liveness_score > 0:
                    self.draw_liveness_indicator(display_frame, bbox, liveness_score, liveness_passed)
        
        # Add disclaimer
        disclaimer = "PoC System - Local Data Only - Do Not Distribute"
        cv2.putText(display_frame, disclaimer, (10, self.window_height - 10),
                   self.font, 0.4, self.colors['text'], 1)
        
        # Show frame
        cv2.imshow(self.window_name, display_frame)
    
    def wait_for_key(self, timeout: int = 1) -> Optional[str]:
        """
        Wait for key press with timeout
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Pressed key character or None
        """
        key = cv2.waitKey(timeout) & 0xFF
        if key != 255:  # Not no key
            return chr(key)
        return None
    
    def handle_key_input(self, key: str) -> Dict[str, Any]:
        """
        Handle keyboard input
        
        Args:
            key: Pressed key character
            
        Returns:
            Action dictionary
        """
        actions = {
            'q': {'action': 'quit'},
            'Q': {'action': 'quit'},
            'e': {'action': 'enroll'},
            'E': {'action': 'enroll'},
            's': {'action': 'save_snapshot'},
            'S': {'action': 'save_snapshot'},
            'r': {'action': 'reset'},
            'R': {'action': 'reset'},
            't': {'action': 'reset_attendance'},
            'T': {'action': 'reset_attendance'},
            'h': {'action': 'help'},
            'H': {'action': 'help'}
        }
        
        return actions.get(key, {'action': 'none'})
    
    def show_help(self):
        """Show help dialog"""
        help_text = [
            "KEYBOARD CONTROLS:",
            "",
            "E - Enroll new user",
            "S - Save snapshot",
            "R - Reset detection",
            "H - Show this help",
            "Q - Quit application",
            "",
            "SYSTEM INFO:",
            f"- Current FPS: {self.state.processing_fps:.1f}",
            f"- Faces detected: {self.state.face_count}",
            f"- Match threshold: 0.70",
            f"- Liveness required: Yes"
        ]
        
        help_img = np.zeros((400, 600, 3), dtype=np.uint8)
        
        y_offset = 30
        for line in help_text:
            if line.startswith("-"):
                color = self.colors['warning']
            elif line.endswith(":"):
                color = self.colors['success']
            else:
                color = self.colors['text']
            
            cv2.putText(help_img, line, (20, y_offset), self.font, 0.6, color, 1)
            y_offset += 25
        
        cv2.imshow("Help", help_img)
        cv2.waitKey(0)
        cv2.destroyWindow("Help")
    
    def cleanup(self):
        """Clean up UI resources"""
        cv2.destroyAllWindows()
    
    def is_window_open(self) -> bool:
        """Check if main window is still open"""
        return cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) >= 1

class CameraInterface:
    """Simple camera interface for testing"""
    
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
    
    def start(self) -> bool:
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            return self.cap.isOpened()
        except Exception as e:
            print(f"Failed to start camera: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get current frame"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def stop(self):
        """Stop camera capture"""
        if self.cap:
            self.cap.release()

# Test function
if __name__ == "__main__":
    # Test UI system
    ui = UISystem()
    
    # Test state updates
    ui.update_state(system_status="Testing...")
    ui.update_state(face_count=1, processing_fps=15.5)
    
    # Test frame display
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    print("UI System initialized")
    print("Press 'Q' to quit, 'H' for help")
    
    while ui.is_window_open():
        key = ui.wait_for_key(1000)  # 1 second timeout
        
        if key:
            action = ui.handle_key_input(key)
            print(f"Key pressed: {key}, Action: {action}")
            
            if action['action'] == 'quit':
                break
            elif action['action'] == 'help':
                ui.show_help()
        
        # Update test frame and show
        import random
        test_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        ui.show_frame(test_frame)
    
    ui.cleanup()
    print("UI test completed")
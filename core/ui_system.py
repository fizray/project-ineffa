import cv2
import numpy as np
import time
from datetime import datetime

class UISystem:
    def __init__(self, config):
        self.config = config
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Colors (B, G, R)
        self.colors = {
            'success': (0, 255, 0),    # Green
            'warning': (0, 255, 255),  # Yellow
            'danger': (0, 0, 255),     # Red
            'text': (255, 255, 255),   # White
            'bg_dark': (0, 0, 0),      # Black
            'accent': (255, 191, 0)    # Deep Sky Blueish
        }
        
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.fps = 0.0

    def update_fps(self):
        self.fps_counter += 1
        elapsed = time.time() - self.fps_start_time
        if elapsed > 1.0:
            self.fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = time.time()

    def draw_dashboard(self, frame, tracked_faces, faces_map, recent_logs, is_connected=True):
        self.update_fps()
        h, w = frame.shape[:2]
        
        # 1. Draw Main Content (Bounding Boxes)
        self._draw_tracking(frame, tracked_faces, faces_map)
        
        # 2. Draw Header (Status Bar)
        self._draw_header(frame, w, is_connected)
        
        # 3. Draw Sidebar (Recent Logs)
        self._draw_sidebar(frame, h, w, recent_logs)
        
        return frame

    def _draw_header(self, frame, width, is_connected):
        # Semi-transparent bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 40), self.colors['bg_dark'], -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # System Title
        cv2.putText(frame, self.config['ui']['window_name'], (15, 28), 
                   self.font, 0.7, self.colors['text'], 2)
        
        # Status Indicators
        status_text = "ONLINE" if is_connected else "OFFLINE"
        status_color = self.colors['success'] if is_connected else self.colors['danger']
        
        # Right aligned status
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (width - 250, 28), 
                   self.font, 0.6, self.colors['accent'], 1)
        
        cv2.circle(frame, (width - 100, 22), 6, status_color, -1)
        cv2.putText(frame, status_text, (width - 85, 28), 
                   self.font, 0.6, status_color, 2)

    def _draw_sidebar(self, frame, height, width, recent_logs):
        sidebar_w = 300
        overlay = frame.copy()
        # Draw sidebar background on the right
        cv2.rectangle(overlay, (width - sidebar_w, 40), (width, height), self.colors['bg_dark'], -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Title
        cv2.putText(frame, "RECENT ACTIVITY", (width - sidebar_w + 15, 70), 
                   self.font, 0.6, self.colors['accent'], 2)
        
        # Logs
        y_start = 110
        for i, log in enumerate(reversed(recent_logs[-10:])): # Show last 10
            name = log['name']
            time_str = log['time']
            
            # Entry background
            # cv2.rectangle(frame, (width - sidebar_w + 10, y_start - 20), (width - 10, y_start + 10), (50, 50, 50), -1)
            
            cv2.putText(frame, name, (width - sidebar_w + 15, y_start), 
                       self.font, 0.6, self.colors['text'], 1)
            cv2.putText(frame, time_str, (width - 100, y_start), 
                       self.font, 0.5, (200, 200, 200), 1)
            
            y_start += 40

    def _draw_tracking(self, frame, tracked_faces, faces_map):
        for object_id, face in faces_map.items():
            if object_id in tracked_faces:
                state = tracked_faces[object_id]
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                
                # Color based on status
                if state['name'] == "SPOOF":
                    color = self.colors['danger']
                    label = "SPOOF"
                    score = f"{state['best_score']:.2f}"
                elif state['name'] != "Unknown":
                    color = self.colors['success']
                    label = state['name']
                    score = f"{state['best_score']:.2f}"
                else:
                    color = self.colors['warning']
                    label = "Unknown"
                    score = ""

                # Fancy Corners
                self._draw_corners(frame, bbox, color)
                
                # Label
                label_text = f"{label} {score}"
                (w, h), _ = cv2.getTextSize(label_text, self.font, 0.6, 1)
                cv2.rectangle(frame, (x1, y1 - 25), (x1 + w + 10, y1), color, -1)
                cv2.putText(frame, label_text, (x1 + 5, y1 - 8), self.font, 0.6, (0,0,0), 2)

    def _draw_corners(self, frame, bbox, color, length=20, thickness=2):
        x1, y1, x2, y2 = bbox
        # Top Left
        cv2.line(frame, (x1, y1), (x1 + length, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + length), color, thickness)
        # Top Right
        cv2.line(frame, (x2, y1), (x2 - length, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + length), color, thickness)
        # Bottom Left
        cv2.line(frame, (x1, y2), (x1 + length, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - length), color, thickness)
        # Bottom Right
        cv2.line(frame, (x2, y2), (x2 - length, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - length), color, thickness)

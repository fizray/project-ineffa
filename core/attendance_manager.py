import time
import logging
from datetime import datetime
import os
import cv2
from PIL import Image, PngImagePlugin
import numpy as np

logger = logging.getLogger("AttendanceManager")

class AttendanceManager:
    def __init__(self, config):
        self.config = config
        self.attendance_log = {}  # {name: last_seen_timestamp}
        self.recent_logs = []     # List of {'name': str, 'time': str} for UI
        self.log_path = self.config['storage']['logs_path']
        self.cooldown = self.config['attendance']['cooldown_seconds']
        
        # Setup captures directory
        self.captures_dir = os.path.join("data", "captures")
        if not os.path.exists(self.captures_dir):
            os.makedirs(self.captures_dir)

        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log_attendance(self, name, frame=None, bbox=None):
        now = time.time()
        
        if name in self.attendance_log:
            last_seen = self.attendance_log[name]
            if now - last_seen < self.cooldown:
                return False  # Cooldown active
        
        self.attendance_log[name] = now
        
        # Prepare log entry
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        time_only_str = timestamp.strftime("%H:%M:%S")
        
        # Capture Face Image
        image_filename = ""
        if frame is not None and bbox is not None:
            image_filename = self._save_face_capture(name, frame, bbox, timestamp)

        # Update UI Log
        self.recent_logs.append({'name': name, 'time': time_only_str})
        if len(self.recent_logs) > 20:
            self.recent_logs.pop(0)
        
        # Write to file
        try:
            with open(self.log_path, "a") as f:
                f.write(f"{timestamp_str},{name},{image_filename}\n")
            logger.info(f"ATTENDANCE LOGGED: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
            return False

    def _save_face_capture(self, name, frame, bbox, timestamp):
        try:
            # Ensure bbox is within frame bounds
            h, w = frame.shape[:2]
            x1, y1, x2, y2 = [int(c) for c in bbox]
            
            # Add some padding
            pad_w = int((x2 - x1) * 0.2)
            pad_h = int((y2 - y1) * 0.2)
            
            x1 = max(0, x1 - pad_w)
            y1 = max(0, y1 - pad_h)
            x2 = min(w, x2 + pad_w)
            y2 = min(h, y2 + pad_h)
            
            face_img = frame[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return ""

            # Convert to RGB for PIL
            face_img_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(face_img_rgb)
            
            # Prepare Metadata
            meta = PngImagePlugin.PngInfo()
            meta.add_text("Name", name)
            meta.add_text("Timestamp", timestamp.isoformat())
            meta.add_text("System", "Ineffa Attendance")
            
            # Generate Filename
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{safe_name}.png"
            filepath = os.path.join(self.captures_dir, filename)
            
            # Save
            pil_img.save(filepath, "PNG", pnginfo=meta)
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save face capture: {e}")
            return ""

    def get_recent_logs(self):
        return self.recent_logs

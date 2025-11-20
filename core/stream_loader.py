import cv2
import threading
import queue
import time
import logging
import os

class RTSPStreamLoader:
    def __init__(self, source, width=1280, height=720, reconnect_delay=5):
        self.source = source
        self.width = width
        self.height = height
        self.reconnect_delay = reconnect_delay
        self.q = queue.Queue(maxsize=1)
        self.stopped = False
        self.thread = None
        self.cap = None
        self.logger = logging.getLogger("StreamLoader")
        self.is_file = False
        self.fps = 30 # Default

    def start(self):
        self.logger.info(f"Starting stream from source: {self.source}")
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        while not self.stopped:
            if self.cap is None or not self.cap.isOpened():
                self._connect()
            
            if not self.cap.isOpened():
                time.sleep(self.reconnect_delay)
                continue

            ret, frame = self.cap.read()
            if not ret:
                if self.is_file:
                    # Loop video file
                    self.logger.info("End of video file. Restarting...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    self.logger.warning("Frame read failed. Reconnecting...")
                    self.cap.release()
                    continue

            # Bufferless logic: remove old frame if exists
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            
            self.q.put(frame)
            
            # If it's a file, limit speed to approximate FPS to avoid burning CPU/skipping too much
            if self.is_file:
                time.sleep(1.0 / self.fps)

        if self.cap:
            self.cap.release()

    def _connect(self):
        try:
            src = self.source
            # Handle integer source for webcams
            if isinstance(self.source, int) or (isinstance(self.source, str) and self.source.isdigit()):
                src = int(self.source)
                self.is_file = False
            elif isinstance(self.source, str):
                # Check if it's a file
                if os.path.exists(self.source):
                    src = os.path.abspath(self.source)
                    self.is_file = True
                    self.logger.info(f"Detected video file source: {src}")
                else:
                    self.is_file = False # Assume RTSP/URL

            self.cap = cv2.VideoCapture(src)
            
            if self.cap.isOpened():
                if self.is_file:
                    self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                    if self.fps <= 0: self.fps = 30
                elif isinstance(src, int):
                    # Set resolution for webcams
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            else:
                self.logger.error(f"Failed to open stream: {self.source}")
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")

    def read(self):
        try:
            return self.q.get(timeout=1.0) # Wait up to 1s for a frame
        except queue.Empty:
            return None

    def stop(self):
        self.stopped = True
        if self.thread:
            self.thread.join()

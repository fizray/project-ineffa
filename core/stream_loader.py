import cv2
import threading
import queue
import time
import logging
import numpy as np

class RTSPStreamLoader:
    """
    Handles video capturing from a webcam or RTSP stream in a separate thread
    to minimize latency and blocking in the main application loop.
    """
    def __init__(self, source, width=1280, height=720, reconnect_delay=5):
        """
        Initializes the RTSPStreamLoader.

        Args:
            source (str or int): The video source. Integer for webcam index, string for RTSP URL.
            width (int): The desired width of the frames.
            height (int): The desired height of the frames.
            reconnect_delay (int): Time in seconds to wait before attempting to reconnect.
        """
        self.source = source
        self.width = width
        self.height = height
        self.reconnect_delay = reconnect_delay
        self.q = queue.Queue(maxsize=1)
        self.stopped = False
        self.thread = None
        self.cap = None
        self.logger = logging.getLogger("StreamLoader")

    def start(self):
        """
        Starts the video capturing thread.

        Returns:
            RTSPStreamLoader: The instance itself.
        """
        self.logger.info(f"Starting stream from source: {self.source}")
        self.thread = threading.Thread(target=self.update, args=(), daemon=True)
        self.thread.start()
        return self

    def update(self):
        """
        The main loop for the capturing thread. Continuously reads frames from the source
        and puts them into a queue. Handles reconnection if the stream drops.
        """
        while not self.stopped:
            if self.cap is None or not self.cap.isOpened():
                self._connect()

            if self.cap is None or not self.cap.isOpened():
                time.sleep(self.reconnect_delay)
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Frame read failed. Reconnecting...")
                if self.cap:
                    self.cap.release()
                self.cap = None
                continue

            # Bufferless logic: remove old frame if exists to keep latency low
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass

            self.q.put(frame)

        if self.cap:
            self.cap.release()

    def _connect(self):
        """
        Attempts to connect to the video source.
        """
        try:
            # Handle integer source for webcams
            if isinstance(self.source, int) or (isinstance(self.source, str) and self.source.isdigit()):
                src = int(self.source)
            else:
                src = self.source

            self.cap = cv2.VideoCapture(src)
            # Set resolution if it's a webcam (might not work for RTSP streams depending on backend)
            if isinstance(src, int):
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            if not self.cap.isOpened():
                self.logger.error(f"Failed to open stream: {self.source}")
        except Exception as e:
            self.logger.error(f"Connection error: {e}")

    def read(self):
        """
        Retrieves the most recent frame from the queue.

        Returns:
            numpy.ndarray or None: The video frame, or None if the queue is empty.
        """
        try:
            return self.q.get(timeout=1.0) # Wait up to 1s for a frame
        except queue.Empty:
            return None

    def stop(self):
        """
        Stops the capturing thread and releases resources.
        """
        self.stopped = True
        if self.thread:
            self.thread.join()

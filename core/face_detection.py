import cv2
import numpy as np
import logging
from insightface.app.common import Face

class FaceDetector:
    """
    A class to handle face detection using the InsightFace library.
    """
    def __init__(self, app, conf_threshold=0.5, nms_threshold=0.4):
        """
        Initializes the FaceDetector.

        Args:
            app (insightface.app.FaceAnalysis): The initialized InsightFace application instance.
            conf_threshold (float): The confidence threshold for filtering detections.
            nms_threshold (float): The Non-Maximum Suppression threshold.
        """
        self.logger = logging.getLogger("FaceDetector")
        self.app = app
        self.conf_threshold = conf_threshold

        # Set NMS threshold for the detection model
        if 'detection' in self.app.models:
            self.app.models['detection'].nms_thresh = nms_threshold

    def detect(self, frame):
        """
        Detects faces in the provided video frame.

        Args:
            frame (numpy.ndarray): The input image/frame.

        Returns:
            list[insightface.app.common.Face]: A list of detected face objects.
            Each object contains bbox, kps, and det_score.
        """
        try:
            # Use the detection model directly to avoid triggering the full recognition pipeline
            # if we only want detection results first.
            det_model = self.app.models['detection']
            bboxes, kpss = det_model.detect(frame, max_num=0, metric='default')

            if bboxes.shape[0] == 0:
                return []

            faces = []
            for i in range(bboxes.shape[0]):
                bbox = bboxes[i, 0:4]
                det_score = bboxes[i, 4]
                kps = None
                if kpss is not None:
                    kps = kpss[i]

                if det_score >= self.conf_threshold:
                    face = Face(bbox=bbox, kps=kps, det_score=det_score)
                    faces.append(face)

            return faces
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            return []

    def draw_faces(self, frame, faces):
        """
        Draws bounding boxes and landmarks for detected faces on the frame.

        Args:
            frame (numpy.ndarray): The input image/frame.
            faces (list[insightface.app.common.Face]): List of face objects to draw.

        Returns:
            numpy.ndarray: The frame with drawings.
        """
        for face in faces:
            bbox = face.bbox.astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

            if face.kps is not None:
                for kp in face.kps:
                    cv2.circle(frame, (int(kp[0]), int(kp[1])), 2, (0, 0, 255), -1)
        return frame

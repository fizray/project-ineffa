import cv2
import numpy as np
import logging
from insightface.app.common import Face

class FaceDetector:
    def __init__(self, app, conf_threshold=0.5, nms_threshold=0.4):
        self.logger = logging.getLogger("FaceDetector")
        self.app = app
        self.conf_threshold = conf_threshold
        
        # Set NMS threshold for the detection model
        if 'detection' in self.app.models:
            self.app.models['detection'].nms_thresh = nms_threshold
        
    def detect(self, frame):
        """
        Detect faces in the frame.
        Returns a list of face objects. Each object has:
        - bbox: [x1, y1, x2, y2]
        - kps: 5 keypoints (landmarks)
        - det_score: confidence score
        """
        try:
            # Use the detection model directly to avoid triggering recognition pipeline
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
        Helper to draw bounding boxes and landmarks on the frame.
        """
        for face in faces:
            bbox = face.bbox.astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            if face.kps is not None:
                for kp in face.kps:
                    cv2.circle(frame, (int(kp[0]), int(kp[1])), 2, (0, 0, 255), -1)
        return frame

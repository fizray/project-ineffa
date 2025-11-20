import numpy as np
import logging
from numpy.linalg import norm

class RecognitionEngine:
    """
    A class to handle facial embedding extraction and similarity computation.
    """
    def __init__(self, app):
        """
        Initializes the RecognitionEngine.

        Args:
            app (insightface.app.FaceAnalysis): The initialized InsightFace application instance.
        """
        self.logger = logging.getLogger("RecognitionEngine")
        self.app = app

    def get_embedding(self, frame, face_obj):
        """
        Extracts the facial embedding for a specific face object from the frame.
        The face_obj must contain 'kps' (keypoints) from the detection step,
        as the model requires them for alignment.

        Args:
            frame (numpy.ndarray): The source image/frame.
            face_obj (insightface.app.common.Face): The detected face object.

        Returns:
            numpy.ndarray or None: The 512-dimensional embedding vector, or None if extraction failed.
        """
        try:
            # InsightFace's recognition model expects the whole frame and the face object (with kps)
            # It performs alignment internally using the keypoints.

            rec_model = self.app.models['recognition']

            # The recognition model's get method: get(img, face)
            # It modifies the face object in-place, adding 'embedding' and 'normed_embedding'.

            rec_model.get(frame, face_obj)
            return face_obj.embedding

        except Exception as e:
            self.logger.error(f"Embedding extraction error: {e}")
            return None

    def compute_similarity(self, embed1, embed2):
        """
        Computes the Cosine Similarity between two embedding vectors.

        Args:
            embed1 (numpy.ndarray or list): The first embedding vector.
            embed2 (numpy.ndarray or list): The second embedding vector.

        Returns:
            float: The cosine similarity score (between -1.0 and 1.0).
        """
        if embed1 is None or embed2 is None:
            return 0.0

        # Ensure they are normalized (ArcFace embeddings usually are, but let's be safe)
        # InsightFace 'normed_embedding' is already normalized. 'embedding' might not be.
        # Cosine Similarity = (A . B) / (||A|| * ||B||)

        # Convert to numpy array if not already (handles lists from JSON)
        if isinstance(embed1, list):
            embed1 = np.array(embed1)
        if isinstance(embed2, list):
            embed2 = np.array(embed2)

        norm1 = norm(embed1)
        norm2 = norm(embed2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(embed1, embed2) / (norm1 * norm2)

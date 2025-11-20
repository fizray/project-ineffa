import numpy as np
from collections import OrderedDict

class CentroidTracker:
    """
    A simple object tracker that uses centroids to track objects across frames.
    It associates objects based on the Euclidean distance between their centroids.
    """
    def __init__(self, max_disappeared=30, max_distance=50):
        """
        Initializes the CentroidTracker.

        Args:
            max_disappeared (int): The number of consecutive frames an object can be lost
                                   before it is deregistered.
            max_distance (int): The maximum distance between centroids to consider them
                                the same object.
        """
        self.next_object_id = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        """
        Registers a new object with a unique ID.

        Args:
            centroid (numpy.ndarray): The (x, y) coordinates of the object's centroid.
        """
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def deregister(self, object_id):
        """
        Removes an object from tracking.

        Args:
            object_id (int): The ID of the object to remove.
        """
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects):
        """
        Updates the tracker with a list of bounding box rectangles from the current frame.

        Args:
            rects (list): A list of bounding boxes in the format [(x1, y1, x2, y2), ...].

        Returns:
            OrderedDict: A dictionary mapping object IDs to their current centroids (x, y).
        """
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return self.objects

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i])
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Compute distance between each pair of object centroids and input centroids
            D = self._compute_distance(np.array(object_centroids), input_centroids)

            # Find smallest value in each row and sort
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue

                if D[row, col] > self.max_distance:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = input_centroids[col]
                self.disappeared[object_id] = 0

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > self.max_disappeared:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(input_centroids[col])

        return self.objects

    def _compute_distance(self, a, b):
        """
        Computes the Euclidean distance matrix between two sets of points.

        Args:
            a (numpy.ndarray): Array of points (N, 2).
            b (numpy.ndarray): Array of points (M, 2).

        Returns:
            numpy.ndarray: Distance matrix (N, M).
        """
        # Euclidean distance
        # a: (N, 2), b: (M, 2)
        # Returns (N, M) distance matrix
        return np.linalg.norm(a[:, None, :] - b[None, :, :], axis=-1)

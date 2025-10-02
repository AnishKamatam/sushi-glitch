"""Fish detection metrics and tracking for sonar analysis."""

import math
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from scipy.spatial import distance as dist


class Detection:
    """Represents a single fish/school detection."""

    def __init__(
        self,
        bbox: Tuple[int, int, int, int],
        area: float,
        density: float,
        tightness: float,
        centroid: Tuple[float, float],
    ):
        self.bbox = bbox  # (x, y, w, h)
        self.area = area
        self.density = density  # mean intensity
        self.tightness = tightness  # compactness/circularity
        self.centroid = centroid
        self.timestamp = None

    def mid_y(self) -> int:
        """Get vertical midpoint of detection."""
        return self.bbox[1] + self.bbox[3] // 2

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'bbox': self.bbox,
            'area': self.area,
            'density': self.density,
            'tightness': self.tightness,
            'centroid': self.centroid,
        }


class CentroidTracker:
    """Simple centroid-based tracker for fish schools."""

    def __init__(self, max_disappeared: int = 5, max_distance: int = 50):
        """
        Initialize tracker.

        Args:
            max_disappeared: Max frames a track can be missing before removal
            max_distance: Max pixel distance to associate detection with track
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # ID -> centroid
        self.disappeared = OrderedDict()  # ID -> frame count
        self.detections_history = OrderedDict()  # ID -> list of detections
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid: Tuple[float, float], detection: Detection):
        """Register a new object with unique ID."""
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.detections_history[self.next_object_id] = [detection]
        self.next_object_id += 1

    def deregister(self, object_id: int):
        """Remove object from tracking."""
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.detections_history:
            del self.detections_history[object_id]

    def update(self, detections: List[Detection]) -> Dict[int, Detection]:
        """
        Update tracker with new detections.

        Args:
            detections: List of Detection objects

        Returns:
            Dictionary mapping track ID to most recent Detection
        """
        # If no detections, mark all as disappeared
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            return {}

        # Input centroids from detections
        input_centroids = np.array([d.centroid for d in detections])

        # If no existing objects, register all
        if len(self.objects) == 0:
            for i in range(len(input_centroids)):
                self.register(input_centroids[i], detections[i])
        else:
            # Get existing object IDs and centroids
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Compute distance matrix
            D = dist.cdist(np.array(object_centroids), input_centroids)

            # Find best matches (Hungarian algorithm simplified)
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
                self.detections_history[object_id].append(detections[col])

                used_rows.add(row)
                used_cols.add(col)

            # Mark unused existing objects as disappeared
            unused_rows = set(range(D.shape[0])) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)

            # Register new detections
            unused_cols = set(range(D.shape[1])) - used_cols
            for col in unused_cols:
                self.register(input_centroids[col], detections[col])

        # Return current tracked objects with their latest detection
        result = {}
        for object_id in self.objects.keys():
            if self.detections_history[object_id]:
                result[object_id] = self.detections_history[object_id][-1]

        return result

    def get_velocity(self, object_id: int) -> Optional[Tuple[float, float]]:
        """
        Get velocity of tracked object (pixels per frame).

        Args:
            object_id: Track ID

        Returns:
            (vx, vy) velocity tuple, or None if insufficient history
        """
        if object_id not in self.detections_history:
            return None

        history = self.detections_history[object_id]
        if len(history) < 2:
            return None

        # Use last 5 detections for smoothing
        recent = history[-5:]
        if len(recent) < 2:
            return None

        dx = recent[-1].centroid[0] - recent[0].centroid[0]
        dy = recent[-1].centroid[1] - recent[0].centroid[1]
        frames = len(recent) - 1

        return (dx / frames, dy / frames)


def preprocess_frame(frame: np.ndarray, config: Dict) -> np.ndarray:
    """
    Preprocess sonar frame for detection.

    Args:
        frame: Input BGR frame
        config: CV configuration dict

    Returns:
        Preprocessed grayscale frame
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Median blur to reduce noise
    blur_kernel = config.get('blur_kernel', 5)
    gray = cv2.medianBlur(gray, blur_kernel)

    # CLAHE for contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=config.get('clahe_clip_limit', 2.0),
        tileGridSize=(config.get('clahe_grid_size', 8),
                      config.get('clahe_grid_size', 8))
    )
    gray = clahe.apply(gray)

    return gray


def detect_fish(frame: np.ndarray, config: Dict) -> List[Detection]:
    """
    Detect fish/schools using classical CV.

    Args:
        frame: Preprocessed grayscale frame
        config: CV configuration dict

    Returns:
        List of Detection objects
    """
    detections = []

    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        frame,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.get('bin_block', 21),
        config.get('bin_c', -5)
    )

    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    area_min = config.get('area_min', 40)
    area_max = config.get('area_max', 20000)
    aspect_max = config.get('aspect_ratio_max', 5.0)

    for contour in contours:
        area = cv2.contourArea(contour)

        # Filter by area
        if area < area_min or area > area_max:
            continue

        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Filter by aspect ratio
        aspect_ratio = max(w, h) / (min(w, h) + 1e-6)
        if aspect_ratio > aspect_max:
            continue

        # Calculate metrics
        # Density: mean intensity in region
        mask = np.zeros(frame.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        density = cv2.mean(frame, mask=mask)[0]

        # Tightness: compactness/circularity (4π*area/perimeter²)
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            tightness = (4 * math.pi * area) / (perimeter * perimeter)
        else:
            tightness = 0.0

        # Centroid
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            cx, cy = x + w // 2, y + h // 2

        detection = Detection(
            bbox=(x, y, w, h),
            area=area,
            density=density,
            tightness=tightness,
            centroid=(cx, cy)
        )

        detections.append(detection)

    return detections


def cluster_detections(detections: List[Detection], merge_distance: int = 30) -> List[Detection]:
    """
    Cluster nearby detections into schools.

    Args:
        detections: List of Detection objects
        merge_distance: Max distance to merge detections

    Returns:
        List of clustered Detection objects
    """
    if len(detections) <= 1:
        return detections

    # Simple agglomerative clustering by distance
    clusters = [[d] for d in detections]

    while True:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Get centroids of clusters
                c1 = np.mean([d.centroid for d in clusters[i]], axis=0)
                c2 = np.mean([d.centroid for d in clusters[j]], axis=0)

                distance = np.linalg.norm(c1 - c2)

                if distance < merge_distance:
                    # Merge clusters
                    clusters[i].extend(clusters[j])
                    del clusters[j]
                    merged = True
                    break
            if merged:
                break
        if not merged:
            break

    # Convert clusters back to Detection objects
    clustered = []
    for cluster in clusters:
        if len(cluster) == 1:
            clustered.append(cluster[0])
        else:
            # Merge into single detection
            all_x = [d.bbox[0] for d in cluster]
            all_y = [d.bbox[1] for d in cluster]
            all_x2 = [d.bbox[0] + d.bbox[2] for d in cluster]
            all_y2 = [d.bbox[1] + d.bbox[3] for d in cluster]

            x1, y1 = min(all_x), min(all_y)
            x2, y2 = max(all_x2), max(all_y2)

            merged_detection = Detection(
                bbox=(x1, y1, x2 - x1, y2 - y1),
                area=sum(d.area for d in cluster),
                density=np.mean([d.density for d in cluster]),
                tightness=np.mean([d.tightness for d in cluster]),
                centroid=(np.mean([d.centroid[0] for d in cluster]),
                          np.mean([d.centroid[1] for d in cluster]))
            )
            clustered.append(merged_detection)

    return clustered


def classify_density(density: float, config: Dict) -> str:
    """
    Classify detection as sparse/moderate/dense.

    Args:
        density: Mean intensity value
        config: Configuration dict

    Returns:
        'sparse', 'moderate', or 'dense'
    """
    threshold = config.get('density_thr', 140.0)

    if density < threshold * 0.7:
        return 'sparse'
    elif density < threshold:
        return 'moderate'
    else:
        return 'dense'


def calculate_school_size(detection: Detection) -> str:
    """
    Estimate school size category.

    Args:
        detection: Detection object

    Returns:
        'small', 'medium', or 'large'
    """
    area = detection.area

    if area < 1000:
        return 'small'
    elif area < 5000:
        return 'medium'
    else:
        return 'large'


if __name__ == "__main__":
    """Test metrics on a synthetic frame."""
    # Create test frame with simulated fish
    test_frame = np.zeros((800, 600), dtype=np.uint8)

    # Add some "fish" blobs
    cv2.circle(test_frame, (300, 400), 30, 200, -1)
    cv2.ellipse(test_frame, (450, 350), (40, 20), 0, 0, 360, 180, -1)
    cv2.rectangle(test_frame, (100, 200), (150, 240), 220, -1)

    # Test detection
    config = {
        'area_min': 40,
        'area_max': 20000,
        'bin_block': 21,
        'bin_c': -5,
        'blur_kernel': 5,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': 8,
        'density_thr': 140.0,
    }

    processed = preprocess_frame(cv2.cvtColor(test_frame, cv2.COLOR_GRAY2BGR), config)
    detections = detect_fish(test_frame, config)

    print(f"Detected {len(detections)} objects:")
    for i, det in enumerate(detections):
        print(f"  Object {i + 1}:")
        print(f"    Area: {det.area:.0f}px²")
        print(f"    Density: {det.density:.1f}")
        print(f"    Tightness: {det.tightness:.2f}")
        print(f"    Size: {calculate_school_size(det)}")
        print(f"    Density class: {classify_density(det.density, config)}")

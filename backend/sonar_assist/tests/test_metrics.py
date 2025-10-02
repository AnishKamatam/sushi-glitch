"""Tests for metrics module."""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import (
    calculate_school_size,
    classify_density,
    cluster_detections,
    detect_fish,
    Detection,
    preprocess_frame,
)


def test_detection_creation():
    """Test Detection object creation."""
    det = Detection(
        bbox=(10, 20, 30, 40),
        area=1200,
        density=150.0,
        tightness=0.8,
        centroid=(25.0, 40.0)
    )

    assert det.bbox == (10, 20, 30, 40)
    assert det.area == 1200
    assert det.density == 150.0
    assert det.tightness == 0.8
    assert det.mid_y() == 40

    print("✓ test_detection_creation passed")


def test_preprocess_frame():
    """Test frame preprocessing."""
    # Create test frame
    frame = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    config = {
        'blur_kernel': 5,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': 8
    }

    processed = preprocess_frame(frame, config)

    assert processed.shape == (600, 800)
    assert processed.dtype == np.uint8
    assert len(processed.shape) == 2  # Grayscale

    print("✓ test_preprocess_frame passed")


def test_detect_fish():
    """Test fish detection on synthetic frame."""
    # Create test frame with simulated fish
    frame = np.zeros((800, 600), dtype=np.uint8)
    cv2.circle(frame, (300, 400), 30, 200, -1)
    cv2.ellipse(frame, (450, 350), (40, 20), 0, 0, 360, 180, -1)

    config = {
        'area_min': 40,
        'area_max': 20000,
        'aspect_ratio_max': 5.0,
        'bin_block': 21,
        'bin_c': -5,
        'density_thr': 140.0
    }

    detections = detect_fish(frame, config)

    assert len(detections) >= 1, f"Expected at least 1 detection, got {len(detections)}"
    assert all(isinstance(d, Detection) for d in detections)

    # Check first detection properties
    if detections:
        det = detections[0]
        assert det.area > 0
        assert 0 <= det.density <= 255
        assert 0 <= det.tightness <= 1

    print(f"✓ test_detect_fish passed (found {len(detections)} detections)")


def test_classify_density():
    """Test density classification."""
    config = {'density_thr': 140.0}

    sparse = classify_density(80.0, config)
    moderate = classify_density(120.0, config)
    dense = classify_density(180.0, config)

    assert sparse == "sparse"
    assert moderate == "moderate"
    assert dense == "dense"

    print("✓ test_classify_density passed")


def test_calculate_school_size():
    """Test school size calculation."""
    small_det = Detection((0, 0, 10, 10), 500, 150, 0.8, (5, 5))
    medium_det = Detection((0, 0, 50, 50), 2500, 150, 0.8, (25, 25))
    large_det = Detection((0, 0, 100, 100), 10000, 150, 0.8, (50, 50))

    assert calculate_school_size(small_det) == "small"
    assert calculate_school_size(medium_det) == "medium"
    assert calculate_school_size(large_det) == "large"

    print("✓ test_calculate_school_size passed")


def test_cluster_detections():
    """Test detection clustering."""
    # Create nearby detections
    det1 = Detection((10, 10, 20, 20), 400, 150, 0.8, (20, 20))
    det2 = Detection((25, 15, 20, 20), 400, 150, 0.8, (35, 25))
    det3 = Detection((200, 200, 20, 20), 400, 150, 0.8, (210, 210))

    detections = [det1, det2, det3]

    # Cluster with small merge distance (should stay separate)
    clustered = cluster_detections(detections, merge_distance=10)
    assert len(clustered) == 3

    # Cluster with large merge distance (should merge first two)
    clustered = cluster_detections(detections, merge_distance=50)
    assert len(clustered) == 2

    print("✓ test_cluster_detections passed")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("Running Metrics Module Tests")
    print("=" * 60 + "\n")

    test_detection_creation()
    test_preprocess_frame()
    test_detect_fish()
    test_classify_density()
    test_calculate_school_size()
    test_cluster_detections()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()

"""Tests for calibration module."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from calibration import DepthCalibrator


def test_calibrator_init():
    """Test calibrator initialization."""
    calibrator = DepthCalibrator()

    assert calibrator is not None
    assert calibrator.calibration_data is not None
    assert 'pix_top' in calibrator.calibration_data
    assert 'pix_bot' in calibrator.calibration_data
    assert 'ft_top' in calibrator.calibration_data
    assert 'ft_bot' in calibrator.calibration_data

    print("✓ test_calibrator_init passed")


def test_pixel_to_depth():
    """Test pixel to depth conversion."""
    calibrator = DepthCalibrator()

    # Set known calibration
    calibrator.calibration_data = {
        'pix_top': 0,
        'pix_bot': 100,
        'ft_top': 0,
        'ft_bot': 100
    }

    # Test linear mapping
    assert calibrator.pixel_to_depth(0) == 0
    assert calibrator.pixel_to_depth(100) == 100
    assert calibrator.pixel_to_depth(50) == 50

    # Test clamping
    assert calibrator.pixel_to_depth(-10) == 0
    assert calibrator.pixel_to_depth(200) == 100

    print("✓ test_pixel_to_depth passed")


def test_depth_to_pixel():
    """Test depth to pixel conversion."""
    calibrator = DepthCalibrator()

    # Set known calibration
    calibrator.calibration_data = {
        'pix_top': 0,
        'pix_bot': 100,
        'ft_top': 0,
        'ft_bot': 100
    }

    # Test linear mapping
    assert calibrator.depth_to_pixel(0) == 0
    assert calibrator.depth_to_pixel(100) == 100
    assert calibrator.depth_to_pixel(50) == 50

    print("✓ test_depth_to_pixel passed")


def test_non_linear_calibration():
    """Test non-zero starting depth."""
    calibrator = DepthCalibrator()

    # Set calibration with offset
    calibrator.calibration_data = {
        'pix_top': 50,
        'pix_bot': 650,
        'ft_top': 0,
        'ft_bot': 100
    }

    # Test mapping
    depth_at_top = calibrator.pixel_to_depth(50)
    depth_at_bottom = calibrator.pixel_to_depth(650)
    depth_at_middle = calibrator.pixel_to_depth(350)

    assert abs(depth_at_top - 0) < 0.1
    assert abs(depth_at_bottom - 100) < 0.1
    assert abs(depth_at_middle - 50) < 1.0  # ~50 feet

    print("✓ test_non_linear_calibration passed")


def test_get_depth_range():
    """Test getting depth range."""
    calibrator = DepthCalibrator()

    calibrator.calibration_data = {
        'pix_top': 50,
        'pix_bot': 650,
        'ft_top': 10,
        'ft_bot': 110
    }

    min_depth, max_depth = calibrator.get_depth_range()

    assert min_depth == 10
    assert max_depth == 110

    print("✓ test_get_depth_range passed")


def test_inverse_operations():
    """Test that depth_to_pixel and pixel_to_depth are inverses."""
    calibrator = DepthCalibrator()

    calibrator.calibration_data = {
        'pix_top': 100,
        'pix_bot': 700,
        'ft_top': 0,
        'ft_bot': 120
    }

    # Test round-trip conversion
    test_depths = [0, 30, 60, 90, 120]

    for depth in test_depths:
        pixel = calibrator.depth_to_pixel(depth)
        recovered_depth = calibrator.pixel_to_depth(pixel)
        assert abs(recovered_depth - depth) < 0.5, f"Round-trip failed for {depth}ft: got {recovered_depth}ft"

    print("✓ test_inverse_operations passed")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 60)
    print("Running Calibration Module Tests")
    print("=" * 60 + "\n")

    test_calibrator_init()
    test_pixel_to_depth()
    test_depth_to_pixel()
    test_non_linear_calibration()
    test_get_depth_range()
    test_inverse_operations()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()

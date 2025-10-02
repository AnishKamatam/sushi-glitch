"""Depth calibration module for pixel-to-feet mapping."""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import yaml


class DepthCalibrator:
    """Handles depth calibration by mapping pixel coordinates to depth in feet."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize calibrator with config file path."""
        self.config_path = config_path or self._get_default_config_path()
        self.calibration_data = self._load_calibration()

    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        module_dir = Path(__file__).parent
        return str(module_dir / "config" / "default.yaml")

    def _load_calibration(self) -> Dict:
        """Load existing calibration from config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('depth_map', {
                    'pix_top': 50,
                    'pix_bot': 650,
                    'ft_top': 0,
                    'ft_bot': 100
                })
        except Exception as e:
            print(f"Warning: Could not load calibration: {e}")
            return {
                'pix_top': 50,
                'pix_bot': 650,
                'ft_top': 0,
                'ft_bot': 100
            }

    def _save_calibration(self):
        """Save calibration to config file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

            config['depth_map'] = self.calibration_data

            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            print(f"✓ Calibration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving calibration: {e}")

    def calibrate_interactive(self, frame: np.ndarray) -> bool:
        """
        Interactive calibration UI.
        User clicks two points (top depth tick and bottom depth tick).

        Args:
            frame: Screenshot/frame to calibrate on

        Returns:
            True if calibration successful, False otherwise
        """
        print("\n=== Depth Calibration ===")
        print("Instructions:")
        print("1. Click on the TOP depth tick mark (e.g., 0 ft or shallowest)")
        print("2. Click on the BOTTOM depth tick mark (e.g., 100 ft or deepest)")
        print("3. Press ESC to cancel")
        print()

        points = []
        window_name = "Depth Calibration - Click 2 Points"

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                points.append((x, y))
                # Draw marker
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                cv2.putText(
                    frame, f"Point {len(points)}", (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                )
                cv2.imshow(window_name, frame)

        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, mouse_callback)
        cv2.imshow(window_name, frame)

        # Wait for 2 clicks or ESC
        while len(points) < 2:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                cv2.destroyAllWindows()
                print("Calibration cancelled.")
                return False

        cv2.destroyAllWindows()

        # Get depth values from user
        try:
            top_depth = float(input(f"Enter depth at TOP point (point 1) in feet: "))
            bottom_depth = float(input(f"Enter depth at BOTTOM point (point 2) in feet: "))

            # Update calibration
            self.calibration_data['pix_top'] = points[0][1]  # Y coordinate
            self.calibration_data['pix_bot'] = points[1][1]  # Y coordinate
            self.calibration_data['ft_top'] = top_depth
            self.calibration_data['ft_bot'] = bottom_depth

            self._save_calibration()

            print(f"\n✓ Calibration complete!")
            print(f"  Top: {points[0][1]}px = {top_depth}ft")
            print(f"  Bottom: {points[1][1]}px = {bottom_depth}ft")

            return True

        except ValueError as e:
            print(f"Invalid input: {e}")
            return False
        except KeyboardInterrupt:
            print("\nCalibration cancelled.")
            return False

    def pixel_to_depth(self, pixel_y: int) -> float:
        """
        Convert pixel Y coordinate to depth in feet.

        Args:
            pixel_y: Y coordinate in pixels

        Returns:
            Depth in feet
        """
        pix_top = self.calibration_data['pix_top']
        pix_bot = self.calibration_data['pix_bot']
        ft_top = self.calibration_data['ft_top']
        ft_bot = self.calibration_data['ft_bot']

        # Linear interpolation
        if pix_bot == pix_top:
            return ft_top

        ratio = (pixel_y - pix_top) / (pix_bot - pix_top)
        depth = ft_top + ratio * (ft_bot - ft_top)

        return max(ft_top, min(ft_bot, depth))

    def depth_to_pixel(self, depth_ft: float) -> int:
        """
        Convert depth in feet to pixel Y coordinate.

        Args:
            depth_ft: Depth in feet

        Returns:
            Y coordinate in pixels
        """
        pix_top = self.calibration_data['pix_top']
        pix_bot = self.calibration_data['pix_bot']
        ft_top = self.calibration_data['ft_top']
        ft_bot = self.calibration_data['ft_bot']

        # Linear interpolation (inverse)
        if ft_bot == ft_top:
            return pix_top

        ratio = (depth_ft - ft_top) / (ft_bot - ft_top)
        pixel = pix_top + ratio * (pix_bot - pix_top)

        return int(pixel)

    def get_depth_range(self) -> Tuple[float, float]:
        """Get calibrated depth range (min, max) in feet."""
        return (
            self.calibration_data['ft_top'],
            self.calibration_data['ft_bot']
        )

    def draw_depth_overlay(self, frame: np.ndarray, y_coord: int, label: str = "") -> np.ndarray:
        """
        Draw depth indicator on frame.

        Args:
            frame: Frame to draw on
            y_coord: Y coordinate to indicate
            label: Optional label text

        Returns:
            Frame with overlay
        """
        depth = self.pixel_to_depth(y_coord)
        text = f"{depth:.1f}ft" if not label else f"{label}: {depth:.1f}ft"

        # Draw horizontal line
        cv2.line(frame, (0, y_coord), (frame.shape[1], y_coord), (0, 255, 255), 2)

        # Draw text background
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (5, y_coord - text_h - 5), (15 + text_w, y_coord + 5), (0, 0, 0), -1)

        # Draw text
        cv2.putText(
            frame, text, (10, y_coord),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
        )

        return frame


if __name__ == "__main__":
    """Test calibration with a sample frame."""
    # Create a test frame
    test_frame = np.zeros((800, 600, 3), dtype=np.uint8)
    cv2.putText(
        test_frame, "Sample Sonar Display", (150, 400),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2
    )

    calibrator = DepthCalibrator()

    # Test interactive calibration
    if calibrator.calibrate_interactive(test_frame.copy()):
        # Test conversion
        print("\nTesting depth conversion:")
        for pixel in [100, 200, 300, 400, 500]:
            depth = calibrator.pixel_to_depth(pixel)
            print(f"  {pixel}px → {depth:.1f}ft")

"""Sonar Assist - Real-time fishing copilot with screen watching.

Main application loop for screen capture, CV detection, Groq refinement, and TTS cues.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import mss
import numpy as np
import yaml
from pynput import keyboard

from calibration import DepthCalibrator
from groq_cv import GroqCV
from metrics import (
    CentroidTracker,
    Detection,
    calculate_school_size,
    classify_density,
    cluster_detections,
    detect_fish,
    preprocess_frame,
)
from tts_elevenlabs import DebounceManager, TTSElevenLabs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SonarAssist:
    """Main application class for real-time sonar analysis."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Sonar Assist.

        Args:
            config_path: Path to config YAML file
        """
        # Load configuration
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

        # Initialize components
        self.calibrator = DepthCalibrator(self.config_path)
        self.groq_cv = GroqCV(
            model_id=self.config['groq']['model_id'],
            endpoint=self.config['groq']['endpoint'],
            timeout=self.config['groq']['timeout_sec']
        )
        self.tts = TTSElevenLabs(
            voice_id=self.config['elevenlabs']['voice_id'],
            model_id=self.config['elevenlabs']['model_id']
        )
        self.debouncer = DebounceManager(
            debounce_sec=self.config['speech']['debounce_sec']
        )

        # Tracking
        self.tracker = CentroidTracker(
            max_disappeared=self.config['tracking']['max_disappeared'],
            max_distance=self.config['tracking']['max_distance']
        )

        # State
        self.roi = None  # (x, y, w, h) Region of Interest
        self.running = False
        self.paused = False
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.show_overlay = True

        # Screen capture
        self.sct = mss.mss()
        self.monitor_index = self.config['capture']['monitor_index']

        logger.info("Sonar Assist initialized")
        self._print_status()

    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        module_dir = Path(__file__).parent
        return str(module_dir / "config" / "default.yaml")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded config from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _print_status(self):
        """Print current status."""
        print("\n" + "=" * 60)
        print("🎣 SONAR ASSIST - Real-Time Fishing Copilot")
        print("=" * 60)
        print(f"✓ Configuration loaded from {self.config_path}")
        print(f"✓ Depth calibration: {self.calibrator.get_depth_range()} ft")
        print(f"✓ Groq CV: {'Enabled' if self.groq_cv.enabled else 'Disabled (no API key)'}")
        print(f"✓ TTS: {'Enabled' if self.tts.enabled else 'Disabled (fallback to text)'}")
        print("\nKeyboard Controls:")
        print("  [R] - Select screen region (ROI)")
        print("  [C] - Calibrate depth mapping")
        print("  [P] - Pause/Resume")
        print("  [O] - Toggle overlay")
        print("  [Q] - Quit")
        print("=" * 60 + "\n")

    def select_roi(self) -> bool:
        """
        Interactive ROI selection.

        Returns:
            True if ROI selected successfully
        """
        print("\n📍 Select screen region for sonar monitoring...")
        print("   1. A screenshot will be captured")
        print("   2. Drag a rectangle around the sonar display")
        print("   3. Press ENTER to confirm, ESC to cancel\n")

        # Capture full screen
        monitor = self.sct.monitors[self.monitor_index + 1]  # +1 because 0 is all monitors
        screenshot = self.sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # Select ROI
        window_name = "Select ROI - Press ENTER when done, ESC to cancel"
        roi = cv2.selectROI(window_name, frame, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()

        if roi[2] > 0 and roi[3] > 0:
            self.roi = roi
            logger.info(f"ROI selected: {self.roi}")
            print(f"✓ ROI set to: x={roi[0]}, y={roi[1]}, w={roi[2]}, h={roi[3]}\n")
            return True
        else:
            print("✗ ROI selection cancelled\n")
            return False

    def calibrate_depth(self):
        """Interactive depth calibration."""
        if self.roi is None:
            print("⚠ Please select ROI first (press R)")
            return

        print("\n📏 Starting depth calibration...")

        # Capture current ROI
        frame = self._capture_roi()
        if frame is None:
            print("✗ Failed to capture frame")
            return

        # Run calibration
        success = self.calibrator.calibrate_interactive(frame)
        if success:
            print("✓ Depth calibration complete\n")
        else:
            print("✗ Depth calibration failed\n")

    def _capture_roi(self) -> Optional[np.ndarray]:
        """
        Capture current ROI from screen.

        Returns:
            BGR frame or None if failed
        """
        if self.roi is None:
            return None

        try:
            monitor = self.sct.monitors[self.monitor_index + 1]
            x, y, w, h = self.roi

            # Adjust ROI to monitor coordinates
            bbox = {
                'left': monitor['left'] + x,
                'top': monitor['top'] + y,
                'width': w,
                'height': h
            }

            screenshot = self.sct.grab(bbox)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            return frame

        except Exception as e:
            logger.error(f"Failed to capture ROI: {e}")
            return None

    async def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[str]]:
        """
        Process single frame: detect, track, decide, generate cue.

        Args:
            frame: Input BGR frame

        Returns:
            (annotated_frame, recommendation_text)
        """
        # Preprocess
        processed = preprocess_frame(frame, self.config['cv'])

        # Classical CV detection
        detections = detect_fish(processed, self.config['cv'])

        # Cluster nearby detections
        detections = cluster_detections(detections)

        # Update tracker
        tracked_objects = self.tracker.update(detections)

        # Groq refinement (optional, sampled)
        groq_result = None
        if self.config['groq']['use_groq']:
            should_query = self.groq_cv.should_query(
                frame_count=self.frame_count,
                sample_rate_hz=self.config['groq']['sample_rate_hz'],
                fps=self.fps
            )

            if should_query and len(detections) > 0:
                # Query Groq on largest detection
                largest = max(detections, key=lambda d: d.area)
                x, y, w, h = largest.bbox
                crop = (x, y, w, h)

                groq_result = await self.groq_cv.analyze(frame, crop=crop)
                logger.debug(f"Groq result: {groq_result}")

        # Generate recommendation
        recommendation = self._generate_recommendation(
            detections, tracked_objects, groq_result
        )

        # Draw overlay
        annotated = self._draw_overlay(frame, detections, tracked_objects, recommendation)

        return annotated, recommendation

    def _generate_recommendation(
        self,
        detections: list,
        tracked_objects: Dict,
        groq_result: Optional[Dict]
    ) -> Optional[str]:
        """
        Generate actionable recommendation based on detections.

        Args:
            detections: List of Detection objects
            tracked_objects: Tracked objects dict
            groq_result: Optional Groq analysis result

        Returns:
            Recommendation text or None
        """
        if not detections:
            return None

        # Filter by Groq if available
        if groq_result and groq_result['class'] in ['debris', 'thermocline']:
            if groq_result['confidence'] > 0.6:
                return f"Likely {groq_result['class']} - ignore for now."

        # Find largest/best detection
        best_detection = max(detections, key=lambda d: d.area * d.tightness)

        # Calculate metrics
        size = calculate_school_size(best_detection)
        density_class = classify_density(best_detection.density, self.config['cv'])
        depth_ft = self.calibrator.pixel_to_depth(best_detection.mid_y())

        # Build recommendation
        if best_detection.tightness >= self.config['decision']['tight_school_compactness']:
            tightness_desc = "tight"
        else:
            tightness_desc = "scattered"

        # Check confidence threshold
        confidence = best_detection.tightness * (best_detection.density / 255.0)
        if confidence < self.config['speech']['min_confidence']:
            return None

        # Generate cue
        if size == "large" and tightness_desc == "tight":
            rec = f"Large, tight school around {depth_ft:.0f} feet. Drop to {depth_ft:.0f} and hold."
        elif size in ["medium", "large"]:
            rec = f"School near {depth_ft:.0f} feet. {density_class.capitalize()} density. Troll through {depth_ft:.0f} feet."
        else:
            rec = f"Small mark at {depth_ft:.0f} feet. Worth checking."

        return rec

    def _draw_overlay(
        self,
        frame: np.ndarray,
        detections: list,
        tracked_objects: Dict,
        recommendation: Optional[str]
    ) -> np.ndarray:
        """
        Draw detection overlay on frame.

        Args:
            frame: Input frame
            detections: List of detections
            tracked_objects: Tracked objects
            recommendation: Recommendation text

        Returns:
            Annotated frame
        """
        if not self.show_overlay:
            return frame

        annotated = frame.copy()

        # Draw detections
        for detection in detections:
            x, y, w, h = detection.bbox
            depth_ft = self.calibrator.pixel_to_depth(detection.mid_y())

            # Box color based on density
            density_class = classify_density(detection.density, self.config['cv'])
            if density_class == "dense":
                color = (0, 255, 0)  # Green
            elif density_class == "moderate":
                color = (0, 255, 255)  # Yellow
            else:
                color = (0, 165, 255)  # Orange

            # Draw box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Draw depth line
            mid_y = detection.mid_y()
            cv2.line(annotated, (0, mid_y), (annotated.shape[1], mid_y), color, 1)

            # Draw label
            size = calculate_school_size(detection)
            label = f"{depth_ft:.0f}ft | {size} | {density_class}"
            cv2.putText(
                annotated, label, (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )

        # Draw recommendation
        if recommendation:
            # Background box
            lines = recommendation.split('. ')
            y_offset = 30
            for line in lines:
                (tw, th), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated, (10, y_offset - th - 5), (20 + tw, y_offset + 5), (0, 0, 0), -1)
                cv2.putText(
                    annotated, line, (15, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
                )
                y_offset += th + 15

        # Draw FPS
        cv2.putText(
            annotated, f"FPS: {self.fps:.1f}", (annotated.shape[1] - 120, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        # Draw status
        status = "PAUSED" if self.paused else "RUNNING"
        cv2.putText(
            annotated, status, (annotated.shape[1] - 120, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if not self.paused else (0, 0, 255), 2
        )

        return annotated

    async def run(self):
        """Main processing loop."""
        if self.roi is None:
            print("⚠ No ROI selected. Press 'R' to select region.")
            return

        self.running = True
        target_fps = self.config['capture']['target_fps']
        frame_time = 1.0 / target_fps

        print(f"🚀 Starting real-time processing at {target_fps} FPS...")
        print("   Press 'Q' to quit\n")

        # Display window
        window_name = "Sonar Assist"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while self.running:
            loop_start = time.time()

            if not self.paused:
                # Capture frame
                frame = self._capture_roi()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue

                # Process frame
                annotated, recommendation = await self.process_frame(frame)

                # Speak recommendation
                if recommendation and self.debouncer.should_speak(recommendation):
                    asyncio.create_task(self.tts.speak(
                        recommendation,
                        debounce_sec=self.config['speech']['debounce_sec']
                    ))

                # Display
                cv2.imshow(window_name, annotated)

                # Update counters
                self.frame_count += 1

                # Calculate FPS
                now = time.time()
                if now - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (now - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = now

            # Handle keyboard
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q or ESC
                self.running = False
            elif key == ord('p'):
                self.paused = not self.paused
                logger.info(f"{'Paused' if self.paused else 'Resumed'}")
            elif key == ord('o'):
                self.show_overlay = not self.show_overlay
                logger.info(f"Overlay: {'ON' if self.show_overlay else 'OFF'}")

            # Frame rate control
            elapsed = time.time() - loop_start
            if elapsed < frame_time:
                await asyncio.sleep(frame_time - elapsed)

        cv2.destroyAllWindows()
        print("\n✓ Sonar Assist stopped")

    def on_key_press(self, key):
        """Handle global keyboard events."""
        try:
            if key.char == 'r':
                asyncio.create_task(self._async_select_roi())
            elif key.char == 'c':
                self.calibrate_depth()
        except AttributeError:
            pass

    async def _async_select_roi(self):
        """Async wrapper for ROI selection."""
        await asyncio.to_thread(self.select_roi)


async def main():
    """Main entry point."""
    app = SonarAssist()

    # Setup keyboard listener
    def on_press(key):
        try:
            if hasattr(key, 'char'):
                if key.char == 'r' and not app.running:
                    app.select_roi()
                elif key.char == 'c' and not app.running:
                    app.calibrate_depth()
                elif key.char == 'q':
                    return False  # Stop listener
        except:
            pass

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Initial setup
    print("Press 'R' to select screen region...")
    while app.roi is None:
        await asyncio.sleep(0.5)

    # Optional: calibrate
    response = input("Calibrate depth now? (y/n): ").strip().lower()
    if response == 'y':
        app.calibrate_depth()

    # Run main loop
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n\n✓ Shutting down...")
    finally:
        listener.stop()


if __name__ == "__main__":
    asyncio.run(main())

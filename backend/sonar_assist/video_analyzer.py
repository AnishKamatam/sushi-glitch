"""Video-based Sonar Assist - Analyze uploaded sonar videos."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import yaml

from calibration import DepthCalibrator
from groq_cv import GroqCV
from metrics import (
    CentroidTracker,
    calculate_school_size,
    classify_density,
    cluster_detections,
    detect_fish,
    preprocess_frame,
)
from tts_elevenlabs import DebounceManager, TTSElevenLabs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoSonarAnalyzer:
    """Analyze sonar videos frame by frame."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize video analyzer."""
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

        self.frame_count = 0

    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        module_dir = Path(__file__).parent
        return str(module_dir / "config" / "default.yaml")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    async def analyze_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        enable_tts: bool = False,
        enable_groq: bool = True,
    ) -> List[Dict]:
        """
        Analyze sonar video and return detections.

        Args:
            video_path: Path to input video file
            output_path: Optional path to save annotated video
            enable_tts: Whether to speak recommendations
            enable_groq: Whether to use Groq for refinement

        Returns:
            List of detection dictionaries per frame
        """
        logger.info(f"Opening video: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        logger.info(f"Video: {width}x{height} @ {fps:.2f} FPS, {total_frames} frames")

        # Setup video writer if output requested
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            logger.info(f"Saving annotated video to: {output_path}")

        all_detections = []
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                logger.info(f"Processing frame {frame_idx}/{total_frames}")

                # Process frame
                detections, recommendation, annotated = await self._process_frame(
                    frame, frame_idx, enable_groq
                )

                # Store detections
                all_detections.append({
                    'frame': frame_idx,
                    'timestamp': frame_idx / fps,
                    'detections': [d.to_dict() for d in detections],
                    'recommendation': recommendation
                })

                # Speak recommendation
                if enable_tts and recommendation and self.debouncer.should_speak(recommendation):
                    await self.tts.speak(recommendation)

                # Write annotated frame
                if writer:
                    writer.write(annotated)

                # Show progress every 30 frames
                if frame_idx % 30 == 0:
                    logger.info(f"Progress: {frame_idx}/{total_frames} ({100*frame_idx/total_frames:.1f}%)")

        finally:
            cap.release()
            if writer:
                writer.release()
                logger.info(f"✓ Annotated video saved to: {output_path}")

        logger.info(f"✓ Analysis complete: {len(all_detections)} frames processed")
        return all_detections

    async def _process_frame(
        self, frame: np.ndarray, frame_idx: int, enable_groq: bool
    ) -> tuple:
        """
        Process a single frame.

        Returns:
            (detections, recommendation, annotated_frame)
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
        if enable_groq and self.config['groq']['use_groq']:
            should_query = self.groq_cv.should_query(
                frame_count=frame_idx,
                sample_rate_hz=self.config['groq']['sample_rate_hz'],
                fps=30  # Assume 30 FPS for sampling
            )

            if should_query and len(detections) > 0:
                largest = max(detections, key=lambda d: d.area)
                x, y, w, h = largest.bbox
                crop = (x, y, w, h)
                groq_result = await self.groq_cv.analyze(frame, crop=crop)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            detections, tracked_objects, groq_result
        )

        # Draw overlay
        annotated = self._draw_overlay(frame, detections, recommendation, frame_idx)

        return detections, recommendation, annotated

    def _generate_recommendation(
        self, detections: list, tracked_objects: Dict, groq_result: Optional[Dict]
    ) -> Optional[str]:
        """Generate actionable recommendation."""
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
            return f"Large, tight school around {depth_ft:.0f} feet. Drop to {depth_ft:.0f} and hold."
        elif size in ["medium", "large"]:
            return f"School near {depth_ft:.0f} feet. {density_class.capitalize()} density."
        else:
            return f"Small mark at {depth_ft:.0f} feet."

    def _draw_overlay(
        self, frame: np.ndarray, detections: list, recommendation: Optional[str], frame_idx: int
    ) -> np.ndarray:
        """Draw detection overlay on frame."""
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

        # Draw frame number
        cv2.putText(
            annotated, f"Frame: {frame_idx}", (annotated.shape[1] - 150, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        return annotated


async def main():
    """CLI for video analysis."""
    if len(sys.argv) < 2:
        print("Usage: python video_analyzer.py <video_path> [output_path]")
        print("\nExample:")
        print("  python video_analyzer.py sonar_video.mp4")
        print("  python video_analyzer.py sonar_video.mp4 analyzed_output.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(video_path).exists():
        print(f"❌ Error: Video file not found: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print("🎣 Sonar Video Analyzer")
    print("=" * 60)
    print(f"Input: {video_path}")
    if output_path:
        print(f"Output: {output_path}")
    print()

    analyzer = VideoSonarAnalyzer()

    # Analyze video
    detections = await analyzer.analyze_video(
        video_path=video_path,
        output_path=output_path,
        enable_tts=False,  # Disable voice for batch processing
        enable_groq=True
    )

    # Print summary
    print("\n" + "=" * 60)
    print("Analysis Summary")
    print("=" * 60)

    frames_with_fish = sum(1 for d in detections if d['detections'])
    total_detections = sum(len(d['detections']) for d in detections)

    print(f"Total frames: {len(detections)}")
    print(f"Frames with fish: {frames_with_fish}")
    print(f"Total detections: {total_detections}")
    print(f"Average detections/frame: {total_detections/len(detections):.2f}")

    # Print notable detections
    print("\nNotable Detections:")
    for d in detections:
        if d['recommendation'] and 'large' in d['recommendation'].lower():
            print(f"  Frame {d['frame']} ({d['timestamp']:.1f}s): {d['recommendation']}")


if __name__ == "__main__":
    asyncio.run(main())

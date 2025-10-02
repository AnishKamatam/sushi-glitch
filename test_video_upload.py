#!/usr/bin/env python3
"""
Simple test script to upload and analyze a sonar video.
Usage: python3 test_video_upload.py path/to/video.mp4
"""

import sys
import requests
from pathlib import Path
import json


def test_video_upload(video_path: str):
    """Test video upload and analysis."""

    print("=" * 60)
    print("🎣 Testing Sonar Video Analysis")
    print("=" * 60)

    # Check if file exists
    if not Path(video_path).exists():
        print(f"❌ Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"📹 Video: {video_path}")
    print(f"📊 Uploading to backend...")

    # Upload video
    url = "http://localhost:8000/api/sonar/analyze-video"

    try:
        with open(video_path, "rb") as f:
            files = {"video": (Path(video_path).name, f, "video/mp4")}
            response = requests.post(url, files=files, timeout=300)

        if response.status_code != 200:
            print(f"❌ Error: API returned status {response.status_code}")
            print(response.text)
            sys.exit(1)

        result = response.json()

        # Print results
        print("\n" + "=" * 60)
        print("✅ Analysis Complete!")
        print("=" * 60)

        print(f"\n📊 Summary:")
        print(f"  Total frames: {result['summary']['total_frames']}")
        print(f"  Frames with fish: {result['summary']['frames_with_fish']}")
        print(f"  Total detections: {result['summary']['total_detections']}")
        print(f"  Avg detections/frame: {result['summary']['avg_detections_per_frame']}")

        print(f"\n🎯 Key Moments:")
        for i, moment in enumerate(result['key_moments'][:5], 1):
            print(f"  {i}. Frame {moment['frame']} ({moment['timestamp']:.1f}s):")
            print(f"     {moment['recommendation']}")

        print(f"\n📹 Videos:")
        print(f"  Original: http://localhost:8000{result['video_url']}")
        print(f"  Analyzed: http://localhost:8000{result['analyzed_video_url']}")

        print(f"\n💡 To download the analyzed video:")
        print(f"  curl 'http://localhost:8000{result['analyzed_video_url']}' -o analyzed_output.mp4")

        print("\n" + "=" * 60)

        # Save full results to JSON
        output_json = Path(video_path).stem + "_analysis.json"
        with open(output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"📝 Full results saved to: {output_json}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend")
        print("   Make sure the backend is running:")
        print("   cd backend && python3 main.py")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out")
        print("   Video might be too long or processing is slow")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_video_upload.py path/to/video.mp4")
        print("\nExample:")
        print("  python3 test_video_upload.py my_fishing_trip.mp4")
        sys.exit(1)

    video_path = sys.argv[1]
    test_video_upload(video_path)

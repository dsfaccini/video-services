#!/usr/bin/env python3
"""
Script to create a sample video file for testing.
This creates a minimal valid MP4 file that can be used in tests.
"""
import subprocess
import sys
from pathlib import Path


def create_sample_video(output_path: str = "sample_video.mp4", duration: int = 5):
    """Create a simple test video using ffmpeg."""
    try:
        # Create a 5-second video with a blue background
        # Using lavfi (libavfilter input) to generate video without needing input files
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s=320x240:d={duration}',  # Blue color, 320x240, 5 seconds
            '-f', 'lavfi',
            '-i', f'sine=frequency=1000:duration={duration}',  # 1kHz sine wave audio
            '-vcodec', 'libx264',  # H.264 video codec
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-acodec', 'aac',  # AAC audio codec
            '-shortest',  # Match shortest stream duration
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully created sample video: {output_path}")
            return True
        else:
            print(f"Error creating video: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg to create sample videos.")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    output_file = script_dir / "sample_video.mp4"
    
    if create_sample_video(str(output_file)):
        print(f"Sample video created at: {output_file}")
        sys.exit(0)
    else:
        print("Failed to create sample video")
        sys.exit(1)
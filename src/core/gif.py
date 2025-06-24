# pyright: reportUnknownMemberType=warning, reportUnknownVariableType=warning, reportUnknownArgumentType=warning, reportAttributeAccessIssue=warning

from typing import Literal, Tuple
import os
import tempfile
import subprocess
import json
import imageio.v3 as iio
import numpy as np
from PIL import Image

def from_video(
    video_bytes: bytes,
    resize: Literal["25%", "50%", "75%", "100%"] = "100%",
    speed: Literal["0.5x", "1x", "2x", "4x"] = "1x",
    fps: int = 8,
    quality: int = 75,
    loop: Literal["forever", "once", "none"] = "forever",
) -> bytes:
    """
    Convert video bytes to GIF with specified options.

    Args:
        video_bytes: Video content as bytes
        resize: Resize percentage (25%, 50%, 75%, 100%)
        speed: Speed multiplier (0.5x, 1x, 2x, 4x)
        fps: Target frames per second (3-10)
        quality: GIF quality (0-100)
        loop: Loop behavior (forever, once, none)

    Returns:
        GIF as bytes

    Raises:
        ValueError: If parameters are invalid or conversion fails
    """
    # Validate parameters
    if not 3 <= fps <= 10:
        raise ValueError("FPS must be between 3 and 10")
    if not 0 <= quality <= 100:
        raise ValueError("Quality must be between 0 and 100")

    # Parse resize percentage
    resize_factor = int(resize.rstrip("%")) / 100

    # Parse speed multiplier
    speed_factor = float(speed.rstrip("x"))

    # Parse loop count
    loop_count = {
        "forever": 0,  # 0 means infinite loop in GIF
        "once": 1,
        "none": -1,  # No loop
    }[loop]

    # Create temporary files
    temp_video_path = tempfile.mktemp(suffix=".mp4")
    temp_gif_path = tempfile.mktemp(suffix=".gif")

    try:
        # Write video bytes to temp file
        with open(temp_video_path, "wb") as f:
            f.write(video_bytes)

        # Get video metadata using imageio v3 with extension hint
        try:
            meta = iio.immeta(temp_video_path, extension=".mp4")
            if os.getenv("DEBUG"):
                print(f"[DEBUG] Video metadata from iio.immeta: {meta}")
        except Exception as meta_error:
            if os.getenv("DEBUG"):
                print(f"[DEBUG] Failed to get metadata with iio.immeta: {meta_error}")
            # Try ffprobe fallback immediately if imageio fails
            try:
                original_width, original_height, video_fps = _get_video_metadata_ffprobe(temp_video_path)
                meta = {"shape": [original_height, original_width], "fps": video_fps}
            except:
                raise ValueError(f"Unable to read video metadata: {meta_error}")

        # Extract dimensions and fps from metadata
        original_width = None
        original_height = None
        video_fps = 30.0  # default fallback
        
        if 'shape' in meta and len(meta['shape']) >= 2:
            original_height, original_width = meta['shape'][:2]
        elif 'size' in meta and len(meta['size']) >= 2:
            original_width, original_height = meta['size'][:2]
        
        if 'fps' in meta:
            video_fps = meta['fps']
        elif 'framerate' in meta:
            video_fps = meta['framerate']
        
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Extracted dimensions: {original_width}x{original_height}, fps: {video_fps}")

        # Check for invalid dimensions
        if original_width is None or original_height is None:
            # Use ffprobe fallback for metadata
            if os.getenv("DEBUG"):
                print("[DEBUG] Dimensions not found in metadata, using ffprobe fallback")
            original_width, original_height, video_fps = _get_video_metadata_ffprobe(temp_video_path)
            
        # Validate dimensions
        if not (isinstance(original_width, (int, float)) and isinstance(original_height, (int, float))):
            raise ValueError(f"Invalid dimension types: width={type(original_width)}, height={type(original_height)}")
            
        if original_width == float('inf') or original_height == float('inf') or original_width <= 0 or original_height <= 0:
            if os.getenv("DEBUG"):
                print(f"[DEBUG] Invalid dimensions detected: {original_width}x{original_height}, using ffprobe fallback")
            original_width, original_height, video_fps = _get_video_metadata_ffprobe(temp_video_path)
            
        # Calculate new dimensions
        new_width = original_width * resize_factor
        new_height = original_height * resize_factor
        
        # Check for overflow/infinity before converting to int
        if not (0 < new_width < float('inf')) or not (0 < new_height < float('inf')):
            raise ValueError(f"Invalid resize calculation: {new_width}x{new_height}")
        
        width = int(new_width)
        height = int(new_height)
        
        if width <= 0 or height <= 0:
            raise ValueError(f"Calculated dimensions too small: {width}x{height}")
            
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Final dimensions: {width}x{height}, video_fps: {video_fps}")

        # Calculate frame sampling based on speed  
        frame_step = int((video_fps / fps) * speed_factor)
        if frame_step < 1:
            frame_step = 1
            
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Frame step: {frame_step}")

        # Read and process frames using imageio v3 imiter
        frames = []
        frame_index = 0
        
        if os.getenv("DEBUG"):
            print("[DEBUG] Starting frame iteration with iio.imiter")
        
        try:
            for frame in iio.imiter(temp_video_path, extension=".mp4"):
                if frame_index % frame_step == 0:
                    # Resize frame if needed
                    if resize_factor != 1.0:
                        # Use PIL for precise resizing
                        img = Image.fromarray(frame)
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        resized = np.array(img)
                        frames.append(resized)
                    else:
                        frames.append(frame)
                
                frame_index += 1
                
                # Safety limit to prevent processing too many frames
                if frame_index > 1000:  # Max 1000 frames
                    if os.getenv("DEBUG"):
                        print("[DEBUG] Reached frame limit of 1000")
                    break
                    
        except Exception as frame_error:
            if os.getenv("DEBUG"):
                print(f"[DEBUG] Error during frame iteration: {frame_error}")
            raise ValueError(f"Failed to process video frames: {frame_error}")
        
        if not frames:
            raise ValueError("No frames could be extracted from the video")
            
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Processed {len(frames)} frames")

        # Write GIF using imageio v3
        if os.getenv("DEBUG"):
            print("[DEBUG] Writing GIF")
            
        # Calculate duration per frame in milliseconds
        duration_ms = int(1000 / fps)

        # Write frames to GIF
        writer = iio.imopen(temp_gif_path, "w", extension=".gif")
        
        for frame in frames:
            writer.write(
                frame,
                duration=duration_ms,  # type: ignore[call-arg]
                loop=loop_count if loop_count >= 0 else None,  # type: ignore[call-arg]
            )

        writer.close()

        # Read GIF bytes
        with open(temp_gif_path, "rb") as f:
            gif_bytes = f.read()
            
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Generated GIF with {len(gif_bytes)} bytes")

        return gif_bytes

    except Exception as e:
        raise ValueError(f"Failed to convert video to GIF: {str(e)}")

    finally:
        # Clean up temporary files
        for path in [temp_video_path, temp_gif_path]:
            if os.path.exists(path):
                os.unlink(path)


def _get_video_metadata_ffprobe(video_path: str) -> Tuple[int, int, float]:
    """
    Get video metadata using ffprobe as fallback when imageio fails.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Tuple of (width, height, fps)
        
    Raises:
        ValueError: If ffprobe fails or returns invalid data
    """
    try:
        if os.getenv("DEBUG"):
            print("[DEBUG] Using ffprobe to get video metadata")
            
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise ValueError(f"ffprobe failed with error: {result.stderr}")
            
        metadata = json.loads(result.stdout)
        
        if not metadata.get('streams'):
            raise ValueError("No video streams found by ffprobe")
            
        stream = metadata['streams'][0]
        width = stream.get('width')
        height = stream.get('height')
        
        # Parse frame rate (might be in format like "30/1")
        fps = 30.0  # default
        if 'r_frame_rate' in stream:
            rate_str = stream['r_frame_rate']
            if '/' in rate_str:
                num, den = rate_str.split('/')
                if int(den) != 0:
                    fps = float(num) / float(den)
            else:
                fps = float(rate_str)
                
        if not width or not height:
            raise ValueError(f"Invalid dimensions from ffprobe: {width}x{height}")
            
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions from ffprobe: {width}x{height}")
            
        if os.getenv("DEBUG"):
            print(f"[DEBUG] ffprobe metadata: {width}x{height} @ {fps}fps")
            
        return int(width), int(height), fps
        
    except subprocess.TimeoutExpired:
        raise ValueError("ffprobe command timed out")
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse ffprobe output: {e}")
    except FileNotFoundError as e:
        if "ffprobe" in str(e):
            raise ValueError("ffprobe not found. Please install ffmpeg.")
        else:
            # File not found - probably in tests
            raise ValueError(f"Video file not found: {video_path}")

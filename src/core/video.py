from typing import Any, Dict, Literal

import os
import tempfile
import yt_dlp
from yt_dlp.utils import download_range_func
import imageio.v3 as iio
import numpy as np


def extract_video_url(post_url: str) -> str:
    """
    Extract direct video URL from social media post URL using yt-dlp.

    Args:
        post_url: URL of the social media post (X.com, LinkedIn, etc.)

    Returns:
        Direct URL of the video file

    Raises:
        ValueError: If video URL cannot be extracted
    """
    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "no_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(post_url, download=False)

            if not info:
                raise ValueError("Could not extract video information")

            # Get the best video format URL
            raw_url = info.get("url")
            if raw_url:
                return raw_url
            elif "formats" in info:
                formats = info.get("formats") or []
                # Select best quality video
                video_formats = [f for f in formats if f.get("vcodec") != "none"]
                if video_formats:
                    best_format = max(video_formats, key=lambda f: f.get("height", 0))
                    return best_format["url"]
                else:
                    # Fallback to any format
                    return info["formats"][0]["url"]
            else:
                raise ValueError("No video URL found in extracted information")

    except Exception as e:
        raise ValueError(f"Failed to extract video URL: {str(e)}")


def clip_video(source_url: str, start_time: float, end_time: float) -> bytes:
    """
    Download and clip a video between specified timestamps using yt-dlp.

    Args:
        source_url: Source URL (either social media post URL or direct video URL)
        start_time: Start time in seconds
        end_time: End time in seconds

    Returns:
        Clipped video as bytes

    Raises:
        ValueError: If video cannot be downloaded or clipped
    """
    if start_time < 0:
        raise ValueError("Start time cannot be negative")
    if end_time <= start_time:
        raise ValueError("End time must be greater than start time")

    # Create temporary file for output
    temp_output_path = tempfile.mktemp(suffix=".mp4")

    try:
        # Use yt-dlp to download and clip the video in one step

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": temp_output_path,
            "format": "best[ext=mp4]/best",
            "download_ranges": download_range_func(None, [(start_time, end_time)]),
            "force_keyframes_at_cuts": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([source_url])

        # Read the clipped video
        with open(temp_output_path, "rb") as f:
            video_bytes = f.read()

        return video_bytes

    except Exception as e:
        raise ValueError(f"Failed to clip video: {str(e)}")

    finally:
        # Clean up temporary files
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)


def make_gif(
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

        # Read video with imageio
        reader = iio.imopen(temp_video_path, "r")
        meta = reader.properties()

        # Calculate output dimensions
        width = int(meta.shape[1] * resize_factor)
        height = int(meta.shape[0] * resize_factor)

        # Calculate frame sampling based on speed
        video_fps = meta.fps
        frame_step = int((video_fps / fps) * speed_factor)
        if frame_step < 1:
            frame_step = 1

        # Read and process frames
        frames = []
        for i, frame in enumerate(reader):
            if i % frame_step == 0:
                # Resize frame if needed
                if resize_factor != 1.0:
                    # Simple resize using numpy slicing
                    resized = frame[
                        :: int(1 / resize_factor), :: int(1 / resize_factor)
                    ]
                    # Ensure dimensions match expected size
                    if resized.shape[0] != height or resized.shape[1] != width:
                        # Use more precise resizing
                        from PIL import Image

                        img = Image.fromarray(frame)
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        resized = np.array(img)
                    frames.append(resized)
                else:
                    frames.append(frame)

        reader.close()

        # Write GIF
        writer = iio.imopen(temp_gif_path, "w", extension=".gif")

        # Calculate duration per frame in milliseconds
        duration_ms = int(1000 / fps)

        # Write frames to GIF
        for frame in frames:
            writer.write(
                frame,
                duration=duration_ms,
                loop=loop_count if loop_count >= 0 else None,
            )

        writer.close()

        # Read GIF bytes
        with open(temp_gif_path, "rb") as f:
            gif_bytes = f.read()

        return gif_bytes

    except Exception as e:
        raise ValueError(f"Failed to convert video to GIF: {str(e)}")

    finally:
        # Clean up temporary files
        for path in [temp_video_path, temp_gif_path]:
            if os.path.exists(path):
                os.unlink(path)


def url_to_gif(
    source_url: str,
    start_time: float,
    end_time: float,
    resize: Literal["25%", "50%", "75%", "100%"] = "100%",
    speed: Literal["0.5x", "1x", "2x", "4x"] = "1x",
    fps: int = 8,
    quality: int = 75,
    loop: Literal["forever", "once", "none"] = "forever",
) -> bytes:
    """
    Convert a video URL to GIF with clipping and specified options.

    Args:
        source_url: Source URL (either social media post URL or direct video URL)
        start_time: Start time in seconds
        end_time: End time in seconds
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
    # First clip the video
    video_bytes = clip_video(source_url, start_time, end_time)

    # Then convert to GIF
    return make_gif(video_bytes, resize, speed, fps, quality, loop)

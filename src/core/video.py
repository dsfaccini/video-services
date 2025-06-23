from typing import Any, Dict

import os
import tempfile
import yt_dlp
import ffmpeg


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
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'no_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(post_url, download=False)
            
            if not info:
                raise ValueError("Could not extract video information")
            
            # Get the best video format URL
            raw_url = info.get('url')
            if raw_url:
                return raw_url
            elif 'formats' in info:
                formats = info.get('formats') or []   
                # Select best quality video
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                if video_formats:
                    best_format = max(video_formats, key=lambda f: f.get('height', 0))
                    return best_format['url']
                else:
                    # Fallback to any format
                    return info['formats'][0]['url']
            else:
                raise ValueError("No video URL found in extracted information")
                
    except Exception as e:
        raise ValueError(f"Failed to extract video URL: {str(e)}")


def clip_video(video_url: str, start_time: float, end_time: float) -> bytes:
    """
    Download and clip a video between specified timestamps.
    
    Args:
        video_url: Direct URL of the video to clip
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
    
    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
        temp_input_path = temp_input.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
        temp_output_path = temp_output.name
    
    try:
        # Download video using yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': temp_input_path,
            'format': 'best[ext=mp4]/best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Clip video using typed-ffmpeg
        duration = end_time - start_time
        
        (
            ffmpeg
            .input(temp_input_path, ss=start_time, t=duration)
            .output(
                temp_output_path,
                codec='copy',  # Copy codecs for speed
                avoid_negative_ts='make_zero'
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # Read the clipped video
        with open(temp_output_path, 'rb') as f:
            video_bytes = f.read()
        
        return video_bytes
        
    except Exception as e:
        raise ValueError(f"Failed to clip video: {str(e)}")
        
    finally:
        # Clean up temporary files
        for path in [temp_input_path, temp_output_path]:
            if os.path.exists(path):
                os.unlink(path)
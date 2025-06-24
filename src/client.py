#!/usr/bin/env python3
"""
Video Services API Client

A convenient HTTPX-based client for interacting with the Video Services API.
Can be used interactively in notebooks or as a standalone script.
"""

import httpx
import json
import tempfile
from pathlib import Path
from typing import Any, Optional, Literal, Union
from urllib.parse import urljoin

from config import Config

default_config = Config.from_env()


class VideoServicesClient:
    """Client for interacting with the Video Services API."""
    
    def __init__(
        self, 
        config: Optional[Config] = None,
        base_url: Optional[str] = None,
        auth: Optional[tuple[str, str]] = None,
        timeout: Optional[float] = None
    ):
        """
        Initialize the client.
        
        Args:
            config: Configuration object (uses default config if None)
            base_url: Override base URL from config
            auth: Override auth from config
            timeout: Override timeout from config
        """
        # Use provided config or default
        if config is None:
            config = default_config
        
        # Allow parameter overrides
        self.base_url = (base_url or config.base_url).rstrip('/')
        self.auth = auth or config.auth
        self.timeout = timeout or config.timeout
        self.config = config
        
        self.client = httpx.Client(
            auth=self.auth,
            timeout=self.timeout,
            follow_redirects=True
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def _url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))
    
    def _resolve_output_path(self, path: Union[str, Path]) -> Path:
        """Resolve output path, using default output directory if relative."""
        path = Path(path)
        if not path.is_absolute():
            # If relative path, put it in the default output directory
            output_dir = Path(self.config.default_output_dir)
            path = output_dir / path
        return path
    
    def health_check(self) -> Any:
        """Check if the API is healthy."""
        response = self.client.get(self._url("/health"))
        response.raise_for_status()
        return response.json()
    
    def get_api_info(self) -> Any:
        """Get API information and available endpoints."""
        response = self.client.get(self._url("/"))
        response.raise_for_status()
        return response.json()
    
    def extract_video_url(self, url: str) -> str:
        """
        Extract direct video URL from a social media post URL.
        
        Args:
            url: Social media post URL (X.com, LinkedIn, etc.)
            
        Returns:
            Direct video URL string
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = self.client.get(
            self._url("/api/video/extract-url"),
            params={"url": url}
        )
        response.raise_for_status()
        
        # Handle both dict response and Response object
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()["video_url"]
        else:
            # Handle Response object case
            data = json.loads(response.content.decode())
            return data["video_url"]
    
    def clip_video(
        self, 
        url: str, 
        start_time: float, 
        end_time: float,
        save_to: Optional[Union[str, Path]] = None
    ) -> bytes:
        """
        Clip a video between specified timestamps.
        
        Args:
            url: Video URL or social media post URL
            start_time: Start time in seconds
            end_time: End time in seconds  
            save_to: Optional path to save the clipped video
            
        Returns:
            Video bytes
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = self.client.get(
            self._url("/api/video/clip"),
            params={
                "url": url,
                "start_time": start_time,
                "end_time": end_time
            }
        )
        response.raise_for_status()
        
        video_bytes = response.content
        
        if save_to:
            save_path = self._resolve_output_path(save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(video_bytes)
            print(f"Saved clipped video to: {save_path}")
        
        return video_bytes
    
    def url_to_gif(
        self,
        url: str,
        start_time: float,
        end_time: float,
        resize: Literal["25%", "50%", "75%", "100%"] = "100%",
        speed: Literal["0.5x", "1x", "2x", "4x"] = "1x", 
        fps: int = 8,
        quality: int = 75,
        loop: Literal["forever", "once", "none"] = "forever",
        save_to: Optional[Union[str, Path]] = None
    ) -> bytes:
        """
        Convert video from URL to GIF with clipping and options.
        
        Args:
            url: Video URL or social media post URL
            start_time: Start time in seconds
            end_time: End time in seconds
            resize: Resize percentage 
            speed: Speed multiplier
            fps: Frames per second (3-10)
            quality: GIF quality (0-100)
            loop: Loop behavior
            save_to: Optional path to save the GIF
            
        Returns:
            GIF bytes
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        response = self.client.get(
            self._url("/api/video/url-to-gif"),
            params={
                "url": url,
                "start_time": start_time,
                "end_time": end_time,
                "resize": resize,
                "speed": speed,
                "fps": fps,
                "quality": quality,
                "loop": loop
            }
        )
        response.raise_for_status()
        
        gif_bytes = response.content
        
        if save_to:
            save_path = self._resolve_output_path(save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(gif_bytes)
            print(f"Saved GIF to: {save_path}")
        
        return gif_bytes
    
    def make_gif_from_file(
        self,
        video_file: Union[str, Path],
        resize: Literal["25%", "50%", "75%", "100%"] = "100%",
        speed: Literal["0.5x", "1x", "2x", "4x"] = "1x",
        fps: int = 8, 
        quality: int = 75,
        loop: Literal["forever", "once", "none"] = "forever",
        save_to: Optional[Union[str, Path]] = None
    ) -> bytes:
        """
        Convert uploaded video file to GIF.
        
        Args:
            video_file: Path to video file to upload
            resize: Resize percentage
            speed: Speed multiplier  
            fps: Frames per second (3-10)
            quality: GIF quality (0-100)
            loop: Loop behavior
            save_to: Optional path to save the GIF
            
        Returns:
            GIF bytes
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        video_path = Path(video_file)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        with open(video_path, 'rb') as f:
            files = {"video": (video_path.name, f, "video/mp4")}
            data = {
                "resize": resize,
                "speed": speed,
                "fps": fps,
                "quality": quality,  
                "loop": loop
            }
            
            response = self.client.post(
                self._url("/api/video/make-gif"),
                files=files,
                data=data
            )
        
        response.raise_for_status()
        
        gif_bytes = response.content
        
        if save_to:
            save_path = self._resolve_output_path(save_to)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(gif_bytes)
            print(f"Saved GIF to: {save_path}")
        
        return gif_bytes


# Convenience functions for quick usage
def create_client(
    config: Optional[Config] = None,
    **overrides
) -> VideoServicesClient:
    """Create a client instance with optional config overrides."""
    return VideoServicesClient(config=config, **overrides)


def quick_extract(url: str, config: Optional[Config] = None, **overrides) -> str:
    """Quick video URL extraction."""
    with create_client(config, **overrides) as client:
        return client.extract_video_url(url)


def quick_clip(
    url: str, 
    start_time: float, 
    end_time: float, 
    save_to: Optional[str] = None,
    config: Optional[Config] = None,
    **overrides
) -> bytes:
    """Quick video clipping."""
    with create_client(config, **overrides) as client:
        return client.clip_video(url, start_time, end_time, save_to)


def quick_gif(
    url: str,
    start_time: float,
    end_time: float,
    save_to: Optional[str] = None,
    config: Optional[Config] = None,
    **options
) -> bytes:
    """Quick GIF creation from URL."""
    # Separate config overrides from gif options
    config_overrides = {k: v for k, v in options.items() if k in ['base_url', 'auth', 'timeout']}
    gif_options = {k: v for k, v in options.items() if k not in config_overrides}
    
    with create_client(config, **config_overrides) as client:
        return client.url_to_gif(url, start_time, end_time, save_to=save_to, **gif_options)


# Example usage for interactive sessions
if __name__ == "__main__":
    # Example usage
    print("Video Services API Client")
    print("=" * 30)
    
    # Load configuration from .env file
    print(f"Base URL: {default_config.base_url}")
    print(f"Auth: {'Enabled' if default_config.auth else 'Disabled'}")
    print(f"Output Directory: {default_config.default_output_dir}")
    print()
    
    with create_client() as client:
        try:
            # Health check
            health = client.health_check()
            print(f"API Health: {health}")
            
            # API info
            info = client.get_api_info()
            print(f"API Info: {info}")
            
            # Example URL extraction (update with a real URL)
            # test_url = "https://x.com/tanmay_jain_/status/1937280608755208430"
            # video_url = client.extract_video_url(test_url)
            # print(f"Extracted URL: {video_url}")
            
            print("\nClient ready for use!")
            print("Create a .env file from .env.example to configure authentication.")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure your API server is running and .env is configured!")
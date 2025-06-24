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
from typing import Optional, Literal, Union
from urllib.parse import urljoin


class VideoServicesClient:
    """Client for interacting with the Video Services API."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        auth: Optional[tuple[str, str]] = None,
        timeout: float = 60.0
    ):
        """
        Initialize the client.
        
        Args:
            base_url: The base URL of the API (default: http://localhost:8000)
            auth: Optional tuple of (username, password) for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(
            auth=auth,
            timeout=timeout,
            follow_redirects=True
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def _url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))
    
    def health_check(self) -> dict:
        """Check if the API is healthy."""
        response = self.client.get(self._url("/health"))
        response.raise_for_status()
        return response.json()
    
    def get_api_info(self) -> dict:
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
            Path(save_to).write_bytes(video_bytes)
            print(f"Saved clipped video to: {save_to}")
        
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
            Path(save_to).write_bytes(gif_bytes)
            print(f"Saved GIF to: {save_to}")
        
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
            Path(save_to).write_bytes(gif_bytes)
            print(f"Saved GIF to: {save_to}")
        
        return gif_bytes


# Convenience functions for quick usage
def create_client(
    base_url: str = "http://localhost:8000",
    auth: Optional[tuple[str, str]] = None
) -> VideoServicesClient:
    """Create a client instance."""
    return VideoServicesClient(base_url=base_url, auth=auth)


def quick_extract(url: str, base_url: str = "http://localhost:8000", auth: Optional[tuple[str, str]] = None) -> str:
    """Quick video URL extraction."""
    with create_client(base_url, auth) as client:
        return client.extract_video_url(url)


def quick_clip(
    url: str, 
    start_time: float, 
    end_time: float, 
    save_to: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    auth: Optional[tuple[str, str]] = None
) -> bytes:
    """Quick video clipping."""
    with create_client(base_url, auth) as client:
        return client.clip_video(url, start_time, end_time, save_to)


def quick_gif(
    url: str,
    start_time: float,
    end_time: float,
    save_to: Optional[str] = None,
    base_url: str = "http://localhost:8000", 
    auth: Optional[tuple[str, str]] = None,
    **options
) -> bytes:
    """Quick GIF creation from URL."""
    with create_client(base_url, auth) as client:
        return client.url_to_gif(url, start_time, end_time, save_to=save_to, **options)


# Example usage for interactive sessions
if __name__ == "__main__":
    # Example usage
    print("Video Services API Client")
    print("=" * 30)
    
    # For local development:
    auth = None
    base_url = "http://localhost:8000"
    
    with create_client(base_url=base_url, auth=auth) as client:
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
            
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure your API server is running!")
import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from pydantic import HttpUrl

from src.routes.video import (
    extract_video_url_endpoint,
    clip_video_endpoint,
    ExtractVideoRequest,
    ClipVideoRequest
)


@pytest.mark.unit
class TestVideoRoutes:
    """Unit tests for video route handlers with mocked core functions."""
    
    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_success(self, mocker):
        """Test successful video URL extraction endpoint."""
        mock_extract = mocker.patch('src.routes.video.extract_video_url')
        mock_extract.return_value = "https://example.com/extracted_video.mp4"
        
        request = ExtractVideoRequest(url=HttpUrl("https://x.com/user/status/123"))
        response = await extract_video_url_endpoint(request)
        
        assert response.video_url == "https://example.com/extracted_video.mp4"
        mock_extract.assert_called_once_with("https://x.com/user/status/123")
    
    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_value_error(self, mocker):
        """Test extraction endpoint with ValueError from core function."""
        mock_extract = mocker.patch('src.routes.video.extract_video_url')
        mock_extract.side_effect = ValueError("Invalid URL format")
        
        request = ExtractVideoRequest(url=HttpUrl("https://invalid.com/post"))
        
        with pytest.raises(HTTPException) as exc_info:
            await extract_video_url_endpoint(request)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid URL format"
    
    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_generic_error(self, mocker):
        """Test extraction endpoint with generic exception."""
        mock_extract = mocker.patch('src.routes.video.extract_video_url')
        mock_extract.side_effect = Exception("Unexpected error")
        
        request = ExtractVideoRequest(url=HttpUrl("https://example.com/post"))
        
        with pytest.raises(HTTPException) as exc_info:
            await extract_video_url_endpoint(request)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_clip_video_endpoint_success(self, mocker):
        """Test successful video clipping endpoint."""
        mock_clip = mocker.patch('src.routes.video.clip_video')
        mock_clip.return_value = b"clipped video bytes"
        
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/video.mp4"),
            start_time=10.0,
            end_time=20.0
        )
        
        response = await clip_video_endpoint(request)
        
        assert response.body == b"clipped video bytes"
        assert response.media_type == "video/mp4"
        assert response.headers["Content-Disposition"] == "attachment; filename=clipped_video.mp4"
        mock_clip.assert_called_once_with(
            "https://example.com/video.mp4",
            10.0,
            20.0
        )
    
    @pytest.mark.asyncio
    async def test_clip_video_endpoint_invalid_times(self, mocker):
        """Test clipping endpoint with invalid time parameters."""
        mock_clip = mocker.patch('src.routes.video.clip_video')
        mock_clip.side_effect = ValueError("End time must be greater than start time")
        
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/video.mp4"),
            start_time=20.0,
            end_time=10.0
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(request)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "End time must be greater than start time"
    
    @pytest.mark.asyncio
    async def test_clip_video_endpoint_download_error(self, mocker):
        """Test clipping endpoint with download error."""
        mock_clip = mocker.patch('src.routes.video.clip_video')
        mock_clip.side_effect = ValueError("Failed to download video")
        
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/nonexistent.mp4"),
            start_time=0.0,
            end_time=10.0
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(request)
        
        assert exc_info.value.status_code == 400
        assert "Failed to download video" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_clip_video_endpoint_generic_error(self, mocker):
        """Test clipping endpoint with generic exception."""
        mock_clip = mocker.patch('src.routes.video.clip_video')
        mock_clip.side_effect = Exception("Unexpected error")
        
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/video.mp4"),
            start_time=0.0,
            end_time=10.0
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(request)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


@pytest.mark.unit
class TestVideoModels:
    """Test Pydantic models used in routes."""
    
    def test_extract_video_request_valid_url(self):
        """Test ExtractVideoRequest with valid URL."""
        request = ExtractVideoRequest(url=HttpUrl("https://x.com/user/status/123"))
        assert str(request.url) == "https://x.com/user/status/123"
    
    def test_extract_video_request_invalid_url(self):
        """Test ExtractVideoRequest with invalid URL."""
        with pytest.raises(ValueError):
            ExtractVideoRequest(url="not-a-url")  # type: ignore[arg-type]
    
    def test_clip_video_request_valid(self):
        """Test ClipVideoRequest with valid parameters."""
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/video.mp4"),
            start_time=0.0,
            end_time=10.5
        )
        assert str(request.url) == "https://example.com/video.mp4"
        assert request.start_time == 0.0
        assert request.end_time == 10.5
    
    def test_clip_video_request_negative_times(self):
        """Test ClipVideoRequest allows negative times (validation in core)."""
        # Pydantic model doesn't validate time logic, core function does
        request = ClipVideoRequest(
            url=HttpUrl("https://example.com/video.mp4"),
            start_time=-5.0,
            end_time=10.0
        )
        assert request.start_time == -5.0
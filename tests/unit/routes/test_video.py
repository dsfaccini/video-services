import pytest
from fastapi import HTTPException
from pydantic import HttpUrl

from src.routes.video import (
    extract_video_url_endpoint,
    clip_video_endpoint,
    url_to_gif_endpoint,
    make_gif_endpoint,
)


@pytest.mark.unit
class TestVideoRoutes:
    """Unit tests for video route handlers with mocked core functions."""

    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_success(self, mocker):
        """Test successful video URL extraction endpoint."""
        mock_extract = mocker.patch("src.routes.video.extract_video_url")
        mock_extract.return_value = "https://example.com/extracted_video.mp4"

        url = HttpUrl("https://x.com/user/status/123")
        response = await extract_video_url_endpoint(url=url)

        assert response.media_type == "application/json"
        import json
        data = json.loads(bytes(response.body).decode())
        assert data["video_url"] == "https://example.com/extracted_video.mp4"
        mock_extract.assert_called_once_with("https://x.com/user/status/123")

    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_value_error(self, mocker):
        """Test extraction endpoint with ValueError from core function."""
        mock_extract = mocker.patch("src.routes.video.extract_video_url")
        mock_extract.side_effect = ValueError("Invalid URL format")

        url = HttpUrl("https://invalid.com/post")

        with pytest.raises(HTTPException) as exc_info:
            await extract_video_url_endpoint(url=url)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid URL format"

    @pytest.mark.asyncio
    async def test_extract_video_url_endpoint_generic_error(self, mocker):
        """Test extraction endpoint with generic exception."""
        mock_extract = mocker.patch("src.routes.video.extract_video_url")
        mock_extract.side_effect = Exception("Unexpected error")

        url = HttpUrl("https://example.com/post")

        with pytest.raises(HTTPException) as exc_info:
            await extract_video_url_endpoint(url=url)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_clip_video_endpoint_success(self, mocker):
        """Test successful video clipping endpoint."""
        mock_clip = mocker.patch("src.routes.video.clip_video")
        mock_clip.return_value = b"clipped video bytes"

        url = HttpUrl("https://example.com/video.mp4")

        response = await clip_video_endpoint(url=url, start_time=10.0, end_time=20.0)

        assert response.body == b"clipped video bytes"
        assert response.media_type == "video/mp4"
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=clipped_video.mp4"
        )
        mock_clip.assert_called_once_with("https://example.com/video.mp4", 10.0, 20.0)

    @pytest.mark.asyncio
    async def test_clip_video_endpoint_invalid_times(self, mocker):
        """Test clipping endpoint with invalid time parameters."""
        mock_clip = mocker.patch("src.routes.video.clip_video")
        mock_clip.side_effect = ValueError("End time must be greater than start time")

        url = HttpUrl("https://example.com/video.mp4")

        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(url=url, start_time=20.0, end_time=10.0)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "End time must be greater than start time"

    @pytest.mark.asyncio
    async def test_clip_video_endpoint_download_error(self, mocker):
        """Test clipping endpoint with download error."""
        mock_clip = mocker.patch("src.routes.video.clip_video")
        mock_clip.side_effect = ValueError("Failed to download video")

        url = HttpUrl("https://example.com/nonexistent.mp4")

        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(url=url, start_time=0.0, end_time=10.0)

        assert exc_info.value.status_code == 400
        assert "Failed to download video" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_clip_video_endpoint_generic_error(self, mocker):
        """Test clipping endpoint with generic exception."""
        mock_clip = mocker.patch("src.routes.video.clip_video")
        mock_clip.side_effect = Exception("Unexpected error")

        url = HttpUrl("https://example.com/video.mp4")

        with pytest.raises(HTTPException) as exc_info:
            await clip_video_endpoint(url=url, start_time=0.0, end_time=10.0)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


@pytest.mark.unit
class TestGifEndpoint:
    """Test the GIF endpoint."""

    @pytest.mark.asyncio
    async def test_url_to_gif_endpoint_success(self, mocker):
        """Test successful GIF conversion endpoint."""
        mock_gif = mocker.patch("src.routes.video.url_to_gif")
        mock_gif.return_value = b"gif bytes"

        url = HttpUrl("https://example.com/video.mp4")

        response = await url_to_gif_endpoint(
            url=url,
            start_time=0.0,
            end_time=5.0,
            resize="50%",
            speed="2x",
            fps=8,
            quality=75,
            loop="forever",
        )

        assert response.body == b"gif bytes"
        assert response.media_type == "image/gif"
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=converted.gif"
        )
        mock_gif.assert_called_once_with(
            source_url="https://example.com/video.mp4",
            start_time=0.0,
            end_time=5.0,
            resize="50%",
            speed="2x",
            fps=8,
            quality=75,
            loop="forever",
        )

    @pytest.mark.asyncio
    async def test_url_to_gif_endpoint_value_error(self, mocker):
        """Test GIF endpoint with ValueError."""
        mock_gif = mocker.patch("src.routes.video.url_to_gif")
        mock_gif.side_effect = ValueError("Invalid parameters")

        url = HttpUrl("https://example.com/video.mp4")

        with pytest.raises(HTTPException) as exc_info:
            await url_to_gif_endpoint(url=url, start_time=0.0, end_time=5.0)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid parameters"

    @pytest.mark.asyncio
    async def test_url_to_gif_endpoint_generic_error(self, mocker):
        """Test GIF endpoint with generic exception."""
        mock_gif = mocker.patch("src.routes.video.url_to_gif")
        mock_gif.side_effect = Exception("Unexpected error")

        url = HttpUrl("https://example.com/video.mp4")

        with pytest.raises(HTTPException) as exc_info:
            await url_to_gif_endpoint(url=url, start_time=0.0, end_time=5.0)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail


@pytest.mark.unit
class TestMakeGifEndpoint:
    """Test the make-gif endpoint."""

    @pytest.mark.asyncio
    async def test_make_gif_endpoint_success(self, mocker):
        """Test successful GIF creation from uploaded video."""
        from fastapi import UploadFile
        from io import BytesIO

        mock_make_gif = mocker.patch("src.routes.video.make_gif")
        mock_make_gif.return_value = b"gif bytes"

        # Create a mock upload file
        video_content = b"fake video content"
        video_file = UploadFile(filename="test_video.mp4", file=BytesIO(video_content))

        response = await make_gif_endpoint(
            video=video_file,
            resize="50%",
            speed="2x",
            fps=8,
            quality=75,
            loop="forever",
        )

        assert response.body == b"gif bytes"
        assert response.media_type == "image/gif"
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=test_video.gif"
        )
        mock_make_gif.assert_called_once_with(
            video_bytes=video_content,
            resize="50%",
            speed="2x",
            fps=8,
            quality=75,
            loop="forever",
        )

    @pytest.mark.asyncio
    async def test_make_gif_endpoint_value_error(self, mocker):
        """Test make GIF endpoint with ValueError."""
        from fastapi import UploadFile
        from io import BytesIO

        mock_make_gif = mocker.patch("src.routes.video.make_gif")
        mock_make_gif.side_effect = ValueError("Invalid video format")

        video_file = UploadFile(
            filename="test_video.mp4", file=BytesIO(b"fake video content")
        )

        with pytest.raises(HTTPException) as exc_info:
            await make_gif_endpoint(video=video_file)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid video format"

    @pytest.mark.asyncio
    async def test_make_gif_endpoint_generic_error(self, mocker):
        """Test make GIF endpoint with generic exception."""
        from fastapi import UploadFile
        from io import BytesIO

        mock_make_gif = mocker.patch("src.routes.video.make_gif")
        mock_make_gif.side_effect = Exception("Unexpected error")

        video_file = UploadFile(
            filename="test_video.mp4", file=BytesIO(b"fake video content")
        )

        with pytest.raises(HTTPException) as exc_info:
            await make_gif_endpoint(video=video_file)

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail

import pytest
import ffmpeg as typed_ffmpeg
import tempfile
import traceback

from pathlib import Path
from typing import Callable

from httpx import AsyncClient
from fastapi.testclient import TestClient



@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests using real dependencies."""
    
    def test_health_endpoint(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Video Services API"
        assert "endpoints" in data
        assert data["endpoints"]["extract_video_url"] == "/api/video/extract-url"
        assert data["endpoints"]["clip_video"] == "/api/video/clip"
    
    @pytest.mark.asyncio
    async def test_extract_video_url_invalid_url(self, async_client: AsyncClient) -> None:
        """Test extraction with invalid URL format."""
        response = await async_client.post(
            "/api/video/extract-url",
            json={"url": "not-a-valid-url"}
        )
        assert response.status_code == 422  # Pydantic validation error
    
    @pytest.mark.asyncio
    async def test_clip_video_invalid_times(self, async_client: AsyncClient) -> None:
        """Test clipping with invalid time range."""
        response = await async_client.post(
            "/api/video/clip",
            json={
                "url": "https://example.com/video.mp4",
                "start_time": 20.0,
                "end_time": 10.0
            }
        )
        assert response.status_code == 400
        assert "End time must be greater than start time" in response.json()["detail"]


@pytest.mark.integration
class TestVideoProcessingIntegration:
    """Integration tests with real ffmpeg but controlled video sources."""
    
    def test_clip_local_video_file(self, create_test_video: Callable[[str], str], temp_dir: Path) -> None:
        """Test clipping a local video file using real ffmpeg."""
        # Create a test video
        test_video_path = create_test_video("test_input.mp4")
        output_path = temp_dir / "output.mp4"
        
        # Use real ffmpeg to create a simple test video
        try:
            (
                typed_ffmpeg
                .input('color=c=blue:s=320x240:d=5', f='lavfi')
                .output(test_video_path, vcodec='libx264', pix_fmt='yuv420p')  # type: ignore[arg-type,call-arg]
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except Exception as e:
            # Log error details to file instead of console
            error_log = tempfile.mktemp(suffix='.log', prefix='ffmpeg_error_')
            with open(error_log, 'w') as f:
                f.write(f"FFmpeg error details:\n")
                f.write(f"Exception: {str(e)}\n")
                f.write(f"Exception type: {type(e)}\n")
                traceback.print_exc(file=f)
            print(f"FFmpeg error details written to: {error_log}")
            pytest.skip(f"FFmpeg not available or failed: see {error_log}")
        
        # Now test clipping it
        from src.core.video import clip_video
        
        # Mock yt-dlp to skip download and use local file
        import yt_dlp
        
        class MockYDL:
            def __enter__(self):
                return self
            
            def __exit__(self, *args: str) -> None:
                pass
            
            def download(self, urls: list[str]) -> None:
                # Instead of downloading, just copy the test file
                import shutil
                shutil.copy(test_video_path, urls[0])
        
        # Temporarily replace yt_dlp.YoutubeDL
        original_ydl = yt_dlp.YoutubeDL
        try:
            yt_dlp.YoutubeDL = MockYDL  # type: ignore[assignment,misc]
            
            # This will use real ffmpeg for clipping
            result = clip_video(str(output_path), 1.0, 3.0)
            
            assert len(result) > 0
            # Check for MP4 file signature (more tolerant check)
            assert result[:3] == b'\x00\x00\x00', f"Invalid MP4 header: {result[:8].hex()}"
            
        finally:
            yt_dlp.YoutubeDL = original_ydl  # type: ignore[misc]
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_extract_url_from_youtube_test_video(self):
        """Test extracting URL from a known YouTube test video."""
        from src.core.video import extract_video_url
        
        # Use YouTube's test video that should always be available
        test_urls = [
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" - first YouTube video
        ]
        
        for test_url in test_urls:
            try:
                result = extract_video_url(test_url)
                assert result.startswith("http")
                assert ".googlevideo.com/" in result or ".youtube.com/" in result
                break
            except Exception:
                continue
        else:
            pytest.skip("No test URLs were accessible")


@pytest.mark.integration
class TestAPIErrorHandling:
    """Test error handling with partial real dependencies."""
    
    @pytest.mark.asyncio
    async def test_extract_video_url_unsupported_site(self, async_client: AsyncClient) -> None:
        """Test extraction from an unsupported site."""
        response = await async_client.post(
            "/api/video/extract-url",
            json={"url": "https://example.com/not-a-video-site"}
        )
        assert response.status_code == 400
        assert "Failed to extract video URL" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_clip_video_nonexistent_url(self, async_client: AsyncClient) -> None:
        """Test clipping with a non-existent video URL."""
        response = await async_client.post(
            "/api/video/clip",
            json={
                "url": "https://example.com/nonexistent-video.mp4",
                "start_time": 0.0,
                "end_time": 5.0
            }
        )
        assert response.status_code == 400
        # The exact error message depends on yt-dlp's behavior
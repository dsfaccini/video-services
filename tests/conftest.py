import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import httpx

from src.app import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Create an async test client for the FastAPI app."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_video_info():
    """Mock video information returned by yt-dlp."""
    return {
        'url': 'https://example.com/video.mp4',
        'formats': [
            {
                'url': 'https://example.com/video_720p.mp4',
                'height': 720,
                'vcodec': 'h264',
                'acodec': 'aac',
                'ext': 'mp4'
            },
            {
                'url': 'https://example.com/video_480p.mp4',
                'height': 480,
                'vcodec': 'h264',
                'acodec': 'aac',
                'ext': 'mp4'
            }
        ],
        'title': 'Test Video',
        'duration': 120
    }


@pytest.fixture
def sample_video_path():
    """Path to a sample video file for testing."""
    return Path(__file__).parent / "fixtures" / "sample_video.mp4"


@pytest.fixture
def mock_yt_dlp_success(mocker, mock_video_info):
    """Mock successful yt-dlp extraction."""
    mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
    mock_instance = mock_ydl.return_value.__enter__.return_value
    mock_instance.extract_info.return_value = mock_video_info
    return mock_instance


@pytest.fixture
def mock_yt_dlp_download_success(mocker, temp_dir):
    """Mock successful yt-dlp download."""
    mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
    mock_instance = mock_ydl.return_value.__enter__.return_value
    
    def download_side_effect(urls):
        # Create a dummy file when download is called
        dummy_file = temp_dir / "downloaded_video.mp4"
        dummy_file.write_bytes(b"fake video content")
        return None
    
    mock_instance.download.side_effect = download_side_effect
    return mock_instance


@pytest.fixture
def mock_ffmpeg_success(mocker):
    """Mock successful ffmpeg operation."""
    mock_run = mocker.patch('ffmpeg.run')
    mock_run.return_value = (b"", b"")  # stdout, stderr
    return mock_run


@pytest.fixture
def create_test_video(temp_dir):
    """Create a simple test video file."""
    def _create_video(filename="test_video.mp4", duration=5):
        video_path = temp_dir / filename
        # Create a minimal valid MP4 file header
        # This is a simplified MP4 that most parsers will recognize
        mp4_header = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom'
        video_path.write_bytes(mp4_header + b'\x00' * 1000)  # Add some dummy content
        return str(video_path)
    
    return _create_video


@pytest.fixture
def vcr_config():
    """VCR configuration for recording HTTP interactions."""
    return {
        'record_mode': 'once',  # Record new interactions once
        'match_on': ['uri', 'method'],
        'filter_headers': ['authorization'],
        'filter_query_parameters': ['api_key'],
        'filter_post_data_parameters': ['api_key'],
        'cassette_library_dir': 'tests/fixtures/vcr_cassettes'
    }
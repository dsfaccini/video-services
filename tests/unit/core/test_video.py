import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.core.video import extract_video_url, clip_video


@pytest.mark.unit
class TestExtractVideoUrl:
    """Unit tests for extract_video_url function with mocked dependencies."""
    
    def test_extract_video_url_success_with_direct_url(self, mock_yt_dlp_success):
        """Test successful video URL extraction when direct URL is available."""
        result = extract_video_url("https://x.com/user/status/123456")
        
        assert result == "https://example.com/video.mp4"
        mock_yt_dlp_success.extract_info.assert_called_once_with(
            "https://x.com/user/status/123456", 
            download=False
        )
    
    def test_extract_video_url_success_with_formats(self, mocker):
        """Test video URL extraction when only formats are available."""
        mock_info = {
            'formats': [
                {'url': 'https://example.com/low.mp4', 'height': 480, 'vcodec': 'h264'},
                {'url': 'https://example.com/high.mp4', 'height': 720, 'vcodec': 'h264'},
                {'url': 'https://example.com/audio.m4a', 'vcodec': 'none'},
            ]
        }
        
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        
        result = extract_video_url("https://linkedin.com/posts/123")
        
        # Should select the highest quality video format
        assert result == "https://example.com/high.mp4"
    
    def test_extract_video_url_no_video_formats(self, mocker):
        """Test extraction when no video formats are available."""
        mock_info = {
            'formats': [
                {'url': 'https://example.com/audio.m4a', 'vcodec': 'none'},
            ]
        }
        
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        
        result = extract_video_url("https://example.com/post")
        
        # Should fallback to first available format
        assert result == "https://example.com/audio.m4a"
    
    def test_extract_video_url_no_info(self, mocker):
        """Test extraction failure when no info is returned."""
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = None
        
        with pytest.raises(ValueError, match="Could not extract video information"):
            extract_video_url("https://example.com/invalid")
    
    def test_extract_video_url_no_formats_or_url(self, mocker):
        """Test extraction failure when no URL or formats are available."""
        mock_info = {'title': 'Video Title'}  # Info without URL or formats
        
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.return_value = mock_info
        
        with pytest.raises(ValueError, match="No video URL found"):
            extract_video_url("https://example.com/post")
    
    def test_extract_video_url_yt_dlp_exception(self, mocker):
        """Test handling of yt-dlp exceptions."""
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.extract_info.side_effect = Exception("Network error")
        
        with pytest.raises(ValueError, match="Failed to extract video URL: Network error"):
            extract_video_url("https://example.com/post")


@pytest.mark.unit
class TestClipVideo:
    """Unit tests for clip_video function with mocked dependencies."""
    
    def test_clip_video_success(self, mocker, temp_dir):
        """Test successful video clipping."""
        # Mock yt-dlp download
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_download = mock_ydl.return_value.__enter__.return_value.download
        mock_download.return_value = None
        
        # Mock ffmpeg operations
        mock_ffmpeg = mocker.patch('ffmpeg')
        mock_input = Mock()
        mock_output = Mock()
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.return_value = None
        
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        
        # Mock tempfile and file operations
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            # Setup temp files
            temp_input = temp_dir / "input.mp4"
            temp_output = temp_dir / "output.mp4"
            temp_input.write_bytes(b"input video")
            temp_output.write_bytes(b"clipped video content")
            
            # Configure mocks
            mock_temp.side_effect = [
                MagicMock(name=str(temp_input)),
                MagicMock(name=str(temp_output))
            ]
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"clipped video content"
                
                result = clip_video("https://example.com/video.mp4", 10.0, 20.0)
        
        assert result == b"clipped video content"
        mock_download.assert_called_once()
        mock_ffmpeg.input.assert_called_once()
        
    def test_clip_video_negative_start_time(self):
        """Test clipping with negative start time."""
        with pytest.raises(ValueError, match="Start time cannot be negative"):
            clip_video("https://example.com/video.mp4", -5.0, 10.0)
    
    def test_clip_video_end_time_before_start(self):
        """Test clipping with end time before start time."""
        with pytest.raises(ValueError, match="End time must be greater than start time"):
            clip_video("https://example.com/video.mp4", 20.0, 10.0)
    
    def test_clip_video_end_time_equals_start(self):
        """Test clipping with end time equal to start time."""
        with pytest.raises(ValueError, match="End time must be greater than start time"):
            clip_video("https://example.com/video.mp4", 10.0, 10.0)
    
    def test_clip_video_download_failure(self, mocker):
        """Test handling of download failures."""
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_instance = mock_ydl.return_value.__enter__.return_value
        mock_instance.download.side_effect = Exception("Download failed")
        
        with patch('tempfile.NamedTemporaryFile'):
            with pytest.raises(ValueError, match="Failed to clip video: Download failed"):
                clip_video("https://example.com/video.mp4", 0.0, 10.0)
    
    def test_clip_video_ffmpeg_failure(self, mocker, temp_dir):
        """Test handling of ffmpeg failures."""
        # Mock successful download
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_ydl.return_value.__enter__.return_value.download.return_value = None
        
        # Mock ffmpeg to raise an exception
        mock_ffmpeg = mocker.patch('ffmpeg')
        mock_input = Mock()
        mock_output = Mock()
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run.side_effect = Exception("FFmpeg error")
        
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            temp_files = [
                MagicMock(name=str(temp_dir / "input.mp4")),
                MagicMock(name=str(temp_dir / "output.mp4"))
            ]
            mock_temp.side_effect = temp_files
            
            with pytest.raises(ValueError, match="Failed to clip video: FFmpeg error"):
                clip_video("https://example.com/video.mp4", 0.0, 10.0)
    
    def test_clip_video_cleanup_on_error(self, mocker, temp_dir):
        """Test that temporary files are cleaned up on error."""
        # Create actual temp files
        temp_input = temp_dir / "input.mp4"
        temp_output = temp_dir / "output.mp4"
        temp_input.write_text("test")
        temp_output.write_text("test")
        
        # Mock to raise an exception
        mock_ydl = mocker.patch('yt_dlp.YoutubeDL')
        mock_ydl.return_value.__enter__.return_value.download.side_effect = Exception("Error")
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.side_effect = [
                MagicMock(name=str(temp_input)),
                MagicMock(name=str(temp_output))
            ]
            
            # Mock os.path.exists and os.unlink to track cleanup
            with patch('os.path.exists') as mock_exists:
                with patch('os.unlink') as mock_unlink:
                    mock_exists.return_value = True
                    
                    with pytest.raises(ValueError):
                        clip_video("https://example.com/video.mp4", 0.0, 10.0)
                    
                    # Verify cleanup was attempted
                    assert mock_unlink.call_count == 2
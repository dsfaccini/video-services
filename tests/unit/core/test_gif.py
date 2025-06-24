import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

from src.core.gif import from_video


@pytest.mark.unit
class TestGifFromVideo:
    """Unit tests for gif.from_video function with mocked dependencies."""

    def test_from_video_success_basic(self, mocker):
        """Test successful GIF conversion with default parameters."""
        # Mock imageio v3 metadata
        mock_metadata = {
            'shape': [480, 720, 3],  # height, width, channels
            'fps': 30.0
        }
        mocker.patch("src.core.gif.iio.immeta", return_value=mock_metadata)
        
        # Mock frames (simulate 3 frames)
        mock_frames = [
            np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8),
            np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8),
            np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8),
        ]
        
        # Mock imageio v3 imiter
        mocker.patch("src.core.gif.iio.imiter", return_value=iter(mock_frames))
        
        # Mock imageio v3 imopen for writer
        mock_writer = MagicMock()
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.return_value = mock_writer
        
        # Mock file operations
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        mock_builtin_open.return_value.read.return_value = b"fake gif bytes"
        
        # Mock tempfile
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        
        # Mock os.path.exists and os.unlink
        mocker.patch("os.path.exists", return_value=True)
        mock_unlink = mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        result = from_video(video_bytes)
        
        assert result == b"fake gif bytes"
        
        # Verify file operations
        mock_builtin_open.assert_any_call("/tmp/video.mp4", "wb")
        mock_builtin_open.assert_any_call("/tmp/output.gif", "rb")
        
        # Verify cleanup
        assert mock_unlink.call_count == 2
        mock_unlink.assert_any_call("/tmp/video.mp4")
        mock_unlink.assert_any_call("/tmp/output.gif")

    def test_from_video_with_custom_parameters(self, mocker):
        """Test GIF conversion with custom resize, speed, fps, quality, and loop parameters."""
        # Mock imageio components
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_properties = MagicMock()
        mock_properties.shape = [480, 720, 3]
        mock_properties.get.return_value = 30.0
        mock_reader.properties.return_value = mock_properties
        
        # Mock frame that will be properly resized (50% of 720x480 = 360x240)
        mock_frame = np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8)
        # Create properly sized resized frame for 50% resize
        mock_resized_frame = np.random.randint(0, 255, (240, 360, 3), dtype=np.uint8)
        mock_reader.__iter__ = MagicMock(return_value=iter([mock_frame]))
        
        # Mock PIL Image for resizing
        mock_pil_image = MagicMock()
        mock_resized_pil = MagicMock()
        mock_pil_image.resize.return_value = mock_resized_pil
        
        mocker.patch("src.core.gif.Image.fromarray", return_value=mock_pil_image)
        mocker.patch("src.core.gif.np.array", return_value=mock_resized_frame)
        
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.side_effect = [mock_reader, mock_writer]
        
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        mock_builtin_open.return_value.read.return_value = b"custom gif bytes"
        
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        result = from_video(
            video_bytes,
            resize="50%",
            speed="2x",
            fps=10,
            quality=90,
            loop="once"
        )
        
        assert result == b"custom gif bytes"
        
        # Verify writer.write was called with correct duration (100ms for 10fps) and loop=1
        # We check the call args instead of exact frame match to avoid array comparison issues
        assert mock_writer.write.called
        call_args = mock_writer.write.call_args
        assert call_args[1]["duration"] == 100
        assert call_args[1]["loop"] == 1

    def test_from_video_with_resize_using_pil(self, mocker):
        """Test GIF conversion with resize that requires PIL processing."""
        # Mock imageio components
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_properties = MagicMock()
        # Use dimensions that will require PIL (not evenly divisible)
        mock_properties.shape = [480, 720, 3]  # 480x720
        mock_properties.get.return_value = 30.0
        mock_reader.properties.return_value = mock_properties
        
        # Create a frame
        frame = np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8)
        mock_reader.__iter__ = MagicMock(return_value=iter([frame]))
        
        # For a 75% resize of 720x480, we get 540x360
        # The numpy slicing approach will use step size 1/0.75 = 1.33...
        # This doesn't result in clean slicing, so we need PIL
        
        # Mock PIL Image
        mock_pil_image = MagicMock()
        mock_resized_image = MagicMock()
        mock_pil_image.resize.return_value = mock_resized_image
        mock_resized_array = np.random.randint(0, 255, (360, 540, 3), dtype=np.uint8)
        
        mock_image_fromarray = mocker.patch("src.core.gif.Image.fromarray", return_value=mock_pil_image)
        mock_np_array = mocker.patch("src.core.gif.np.array", return_value=mock_resized_array)
        
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.side_effect = [mock_reader, mock_writer]
        
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        mock_builtin_open.return_value.read.return_value = b"resized gif bytes"
        
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        result = from_video(video_bytes, resize="75%")
        
        assert result == b"resized gif bytes"
        
        # For 75% resize, PIL should be used since numpy slicing won't create exact dimensions
        mock_image_fromarray.assert_called_once_with(frame)
        mock_pil_image.resize.assert_called_once_with((540, 360), mocker.ANY)
        mock_np_array.assert_called_once_with(mock_resized_image)

    def test_from_video_invalid_fps(self):
        """Test that invalid FPS values raise ValueError."""
        with pytest.raises(ValueError, match="FPS must be between 3 and 10"):
            from_video(b"fake video", fps=2)
            
        with pytest.raises(ValueError, match="FPS must be between 3 and 10"):
            from_video(b"fake video", fps=11)

    def test_from_video_invalid_quality(self):
        """Test that invalid quality values raise ValueError."""
        with pytest.raises(ValueError, match="Quality must be between 0 and 100"):
            from_video(b"fake video", quality=-1)
            
        with pytest.raises(ValueError, match="Quality must be between 0 and 100"):
            from_video(b"fake video", quality=101)

    def test_from_video_exception_handling_and_cleanup(self, mocker):
        """Test that exceptions are properly handled and temp files are cleaned up."""
        # Mock tempfile creation
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        
        # Mock file write to succeed
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        
        # Mock imageio to raise an exception
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.side_effect = Exception("Imageio error")
        
        # Mock cleanup functions
        mocker.patch("os.path.exists", return_value=True)
        mock_unlink = mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        
        with pytest.raises(ValueError, match="Failed to convert video to GIF: Imageio error"):
            from_video(video_bytes)
        
        # Verify cleanup happened even with exception
        assert mock_unlink.call_count == 2
        mock_unlink.assert_any_call("/tmp/video.mp4")
        mock_unlink.assert_any_call("/tmp/output.gif")

    def test_from_video_speed_parameter_variations(self, mocker):
        """Test different speed parameter values."""
        # Test different speed values
        speed_tests = ["0.5x", "1x", "2x", "4x"]
        
        for speed in speed_tests:
            # Mock imageio components for each iteration
            mock_reader = MagicMock()
            mock_writer = MagicMock()
            mock_properties = MagicMock()
            mock_properties.shape = [480, 720, 3]
            mock_properties.get.return_value = 30.0  # 30 fps
            mock_reader.properties.return_value = mock_properties
            
            # Create multiple frames to test frame stepping
            mock_frames = [np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8) for _ in range(10)]
            mock_reader.__iter__ = MagicMock(return_value=iter(mock_frames))
            
            mock_imopen = mocker.patch("src.core.gif.iio.imopen")
            mock_imopen.side_effect = [mock_reader, mock_writer]
            
            mock_builtin_open = mocker.patch("builtins.open", mock_open())
            mock_builtin_open.return_value.read.return_value = b"speed test gif"
            
            mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.unlink")
            
            result = from_video(b"fake video", speed=speed, fps=8)  # type: ignore[arg-type]
            assert result == b"speed test gif"
            # Verify that writer.write was called (frames were processed)
            assert mock_writer.write.called

    def test_from_video_loop_parameter_variations(self, mocker):
        """Test different loop parameter values."""
        loop_tests = [
            ("forever", 0),
            ("once", 1),
            ("none", None)
        ]
        
        for loop_value, expected_loop in loop_tests:
            # Mock imageio components for each iteration
            mock_reader = MagicMock()
            mock_writer = MagicMock()
            mock_properties = MagicMock()
            mock_properties.shape = [480, 720, 3]
            mock_properties.get.return_value = 30.0
            mock_reader.properties.return_value = mock_properties
            
            mock_frame = np.random.randint(0, 255, (480, 720, 3), dtype=np.uint8)
            mock_reader.__iter__ = MagicMock(return_value=iter([mock_frame]))
            
            mock_imopen = mocker.patch("src.core.gif.iio.imopen")
            mock_imopen.side_effect = [mock_reader, mock_writer]
            
            mock_builtin_open = mocker.patch("builtins.open", mock_open())
            mock_builtin_open.return_value.read.return_value = b"loop test gif"
            
            mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
            mocker.patch("os.path.exists", return_value=True)
            mocker.patch("os.unlink")
            
            result = from_video(b"fake video", loop=loop_value)  # type: ignore[arg-type]
            assert result == b"loop test gif"
            
            # Verify the correct loop parameter was used
            assert mock_writer.write.called
            call_args = mock_writer.write.call_args
            assert call_args[1]["duration"] == 125
            assert call_args[1]["loop"] == expected_loop

    def test_from_video_invalid_dimensions(self, mocker):
        """Test that invalid video dimensions are handled properly."""
        # Mock imageio components with invalid dimensions
        mock_reader = MagicMock()
        mock_properties = MagicMock()
        mock_properties.shape = [0, 720, 3]  # Invalid height
        mock_reader.properties.return_value = mock_properties
        
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.return_value = mock_reader
        
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        
        with pytest.raises(ValueError, match="Invalid video dimensions"):
            from_video(video_bytes)

    def test_from_video_missing_shape_attribute(self, mocker):
        """Test that missing shape attribute is handled properly."""
        # Mock imageio components without shape attribute
        mock_reader = MagicMock()
        mock_properties = MagicMock()
        # Remove shape attribute
        del mock_properties.shape
        mock_reader.properties.return_value = mock_properties
        
        mock_imopen = mocker.patch("src.core.gif.iio.imopen")
        mock_imopen.return_value = mock_reader
        
        mock_builtin_open = mocker.patch("builtins.open", mock_open())
        mocker.patch("tempfile.mktemp", side_effect=["/tmp/video.mp4", "/tmp/output.gif"])
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.unlink")
        
        video_bytes = b"fake video content"
        
        with pytest.raises(ValueError, match="Unable to determine video dimensions"):
            from_video(video_bytes)
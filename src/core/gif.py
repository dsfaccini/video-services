# pyright: reportUnknownMemberType=warning, reportUnknownVariableType=warning, reportUnknownArgumentType=warning, reportAttributeAccessIssue=warning

from typing import Literal, Any
import os
import tempfile
import imageio.v3 as iio
import numpy as np
from PIL import Image

def from_video(
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
        
        # Debug: Log metadata information in development mode
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Video metadata: shape={getattr(meta, 'shape', 'N/A')}, fps={getattr(meta, 'fps', 'N/A')}")
            print(f"[DEBUG] Available metadata attributes: {dir(meta)}")

        # Calculate output dimensions with validation
        try:
            if not hasattr(meta, 'shape') or len(meta.shape) < 2:
                raise ValueError("Unable to determine video dimensions")
            
            original_width = meta.shape[1]
            original_height = meta.shape[0]
            
            # Check for infinity in original dimensions
            if not (isinstance(original_width, (int, float)) and isinstance(original_height, (int, float))):
                raise ValueError(f"Invalid dimension types: width={type(original_width)}, height={type(original_height)}")
            
            if original_width == float('inf') or original_height == float('inf'):
                # Fallback: Try to get dimensions from first frame
                if os.getenv("DEBUG"):
                    print("[DEBUG] Metadata contains infinite dimensions, trying to get dimensions from first frame")
                try:
                    # Try different methods to get the first frame
                    first_frame = None
                    
                    # Method 1: Try to read first frame directly
                    if hasattr(reader, 'read'):
                        try:
                            first_frame = reader.read()
                        except:
                            pass
                    
                    # Method 2: Try using get_data if available
                    if first_frame is None and hasattr(reader, 'get_data'):
                        try:
                            first_frame = reader.get_data(0)
                        except:
                            pass
                    
                    # Method 3: Try reopening as a different reader type
                    if first_frame is None:
                        try:
                            temp_reader = iio.imread(temp_video_path, index=0)
                            if hasattr(temp_reader, 'shape'):
                                first_frame = temp_reader
                        except:
                            pass
                    
                    if first_frame is not None and hasattr(first_frame, 'shape') and len(first_frame.shape) >= 2:
                        original_height, original_width = first_frame.shape[:2]
                        if os.getenv("DEBUG"):
                            print(f"[DEBUG] Got dimensions from first frame: {original_width}x{original_height}")
                        
                        if original_width == float('inf') or original_height == float('inf'):
                            raise ValueError(f"First frame also contains infinite dimensions: {original_width}x{original_height}")
                    else:
                        raise ValueError("Could not get dimensions from first frame using any method")
                        
                except Exception as frame_error:
                    raise ValueError(f"Video metadata contains infinite dimensions and fallback failed: {original_width}x{original_height}, frame error: {frame_error}")
                    
                # Reset reader position after reading first frame
                reader.close()
                reader = iio.imopen(temp_video_path, "r")
            
            if original_width <= 0 or original_height <= 0:
                raise ValueError(f"Invalid video dimensions: {original_width}x{original_height}")
            
            # Calculate new dimensions
            new_width = original_width * resize_factor
            new_height = original_height * resize_factor
            
            # Check for overflow/infinity before converting to int
            if not (0 < new_width < float('inf')) or not (0 < new_height < float('inf')):
                raise ValueError(f"Invalid resize calculation: {new_width}x{new_height}")
            
            width = int(new_width)
            height = int(new_height)
            
            if width <= 0 or height <= 0:
                raise ValueError(f"Calculated dimensions too small: {width}x{height}")
                
        except (AttributeError, IndexError, TypeError) as e:
            raise ValueError(f"Unable to determine video dimensions: {str(e)}")
        except OverflowError as e:
            raise ValueError(f"Video dimensions too large for processing: {str(e)}")

        # Calculate frame sampling based on speed  
        video_fps = getattr(meta, 'fps', 30.0)
        frame_step = int((video_fps / fps) * speed_factor)
        if frame_step < 1:
            frame_step = 1

        # Read and process frames
        frames = []
        frame: Any
        
        # Try different methods to iterate through frames
        frame_index = 0
        while True:
            try:
                # Try to get frame by index
                if hasattr(reader, 'get_data'):
                    frame = reader.get_data(frame_index)
                elif hasattr(reader, 'read'):
                    frame = reader.read()
                    if frame is None:
                        break
                else:
                    # Try using imageio imread with index
                    frame = iio.imread(temp_video_path, index=frame_index)
                
                i = frame_index
                
            except (IndexError, StopIteration, Exception):
                # No more frames available
                break
                
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
                        img = Image.fromarray(frame)
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        resized = np.array(img)
                    frames.append(resized)
                else:
                    frames.append(frame)
            
            frame_index += 1
            
            # Safety limit to prevent infinite loops
            if frame_index > 1000:  # Max 1000 frames
                break

        reader.close()

        # Write GIF
        writer = iio.imopen(temp_gif_path, "w", extension=".gif")

        # Calculate duration per frame in milliseconds
        duration_ms = int(1000 / fps)

        # Write frames to GIF
        for frame in frames:
            writer.write(
                frame,
                duration=duration_ms,  # type: ignore[call-arg]
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

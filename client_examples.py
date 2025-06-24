"""
Example usage of the Video Services API Client

Copy these examples into your notebook or use them as reference.
"""

from client import VideoServicesClient, quick_extract, quick_clip, quick_gif
from config import Config, config

# Example URLs to test with
EXAMPLE_URLS = {
    "linkedin": "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/",
    "twitter": "https://x.com/tanmay_jain_/status/1937280608755208430",
    "youtube": "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # First YouTube video
}

def example_1_basic_usage():
    """Basic usage with the client."""
    print("=== Example 1: Basic Usage ===")
    
    with VideoServicesClient() as client:
        # Health check
        health = client.health_check()
        print(f"API Health: {health}")
        
        # Get API info
        info = client.get_api_info()
        print(f"Available endpoints: {list(info['endpoints'].keys())}")

def example_2_extract_video_url():
    """Extract video URL from social media."""
    print("=== Example 2: Extract Video URL ===")
    
    test_url = EXAMPLE_URLS["twitter"]  # Change this to test different URLs
    
    with VideoServicesClient() as client:
        try:
            video_url = client.extract_video_url(test_url)
            print(f"Original URL: {test_url}")
            print(f"Extracted Video URL: {video_url}")
            
            # Copy to clipboard if pyperclip is available
            try:
                import pyperclip
                pyperclip.copy(video_url)
                print("✓ Video URL copied to clipboard!")
            except ImportError:
                print("(Install pyperclip to auto-copy URLs)")
                
        except Exception as e:
            print(f"Error extracting video: {e}")

def example_3_clip_video():
    """Clip a video and save it."""
    print("=== Example 3: Clip Video ===")
    
    # First extract a video URL
    test_url = EXAMPLE_URLS["twitter"]
    
    with VideoServicesClient() as client:
        try:
            # Extract video URL first
            video_url = client.extract_video_url(test_url)
            print(f"Using video URL: {video_url[:60]}...")
            
            # Clip first 5 seconds
            video_bytes = client.clip_video(
                url=video_url,
                start_time=0.0,
                end_time=5.0,
                save_to="clipped_video.mp4"
            )
            
            print(f"Clipped video size: {len(video_bytes)} bytes")
            print("✓ Video saved as 'clipped_video.mp4'")
            
        except Exception as e:
            print(f"Error clipping video: {e}")

def example_4_create_gif_from_url():
    """Create a GIF from a video URL."""
    print("=== Example 4: Create GIF from URL ===")
    
    test_url = EXAMPLE_URLS["twitter"]
    
    with VideoServicesClient() as client:
        try:
            # Create GIF with custom options
            gif_bytes = client.url_to_gif(
                url=test_url,
                start_time=0.0,
                end_time=3.0,
                resize="50%",  # Make it smaller
                speed="2x",    # Double speed
                fps=10,        # Higher quality
                quality=80,
                loop="forever",
                save_to="output.gif"
            )
            
            print(f"GIF size: {len(gif_bytes)} bytes")
            print("✓ GIF saved as 'output.gif'")
            
        except Exception as e:
            print(f"Error creating GIF: {e}")

def example_5_create_gif_from_file():
    """Create a GIF from a local video file."""
    print("=== Example 5: Create GIF from File ===")
    
    # This assumes you have a local video file
    video_file = "clipped_video.mp4"  # From previous example
    
    with VideoServicesClient() as client:
        try:
            gif_bytes = client.make_gif_from_file(
                video_file=video_file,
                resize="75%",
                speed="1x",
                fps=8,
                quality=75,
                loop="forever",
                save_to="from_file.gif"
            )
            
            print(f"GIF size: {len(gif_bytes)} bytes")
            print("✓ GIF saved as 'from_file.gif'")
            
        except FileNotFoundError:
            print(f"Video file '{video_file}' not found. Run example 3 first!")
        except Exception as e:
            print(f"Error creating GIF from file: {e}")

def example_6_quick_functions():
    """Use the quick convenience functions."""
    print("=== Example 6: Quick Functions ===")
    
    test_url = EXAMPLE_URLS["twitter"]
    
    try:
        # Quick extract
        video_url = quick_extract(test_url)
        print(f"Quick extracted: {video_url[:60]}...")
        
        # Quick clip (saves to file)
        quick_clip(
            url=video_url,
            start_time=0.0,
            end_time=2.0,
            save_to="quick_clip.mp4"
        )
        print("✓ Quick clip saved")
        
        # Quick GIF
        quick_gif(
            url=test_url,
            start_time=0.0,
            end_time=2.0,
            save_to="quick.gif",
            resize="50%",
            speed="2x"
        )
        print("✓ Quick GIF saved")
        
    except Exception as e:
        print(f"Error with quick functions: {e}")

def run_all_examples():
    """Run all examples in sequence."""
    examples = [
        example_1_basic_usage,
        example_2_extract_video_url,
        example_3_clip_video,
        example_4_create_gif_from_url,
        example_5_create_gif_from_file,
        example_6_quick_functions
    ]
    
    for example in examples:
        try:
            example()
            print()
        except Exception as e:
            print(f"Example failed: {e}")
            print()

if __name__ == "__main__":
    print("Video Services API Client Examples")
    print("=" * 40)
    print(f"Base URL: {config.base_url}")
    print(f"Auth: {'Enabled' if config.auth else 'Disabled'}")
    print(f"Output Directory: {config.default_output_dir}")
    print()
    
    # Run a simple test
    example_1_basic_usage()
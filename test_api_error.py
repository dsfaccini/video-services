#!/usr/bin/env python3
"""Test the API with Instagram URL to get detailed error traceback."""

import os
import httpx

# Set debug mode
os.environ["DEBUG"] = "1"

from src.client import VideoServicesClient

def test_instagram_gif():
    """Test Instagram video to GIF conversion and capture error details."""
    client = VideoServicesClient()
    
    video_url = "https://scontent-mia3-3.cdninstagram.com/o1/v/t16/f2/m86/AQP9reFnQug56kmmlvsembuVI7sn3AlS7IQJQgBrRWEynfaIRyXu_4DD0La0JLTSe9Ywbb2i8oSDN9LKUTQiKBaaPKicCCRlpFu7ayU.mp4?stp=dst-mp4&efg=eyJxZV9ncm91cHMiOiJbXCJpZ193ZWJfZGVsaXZlcnlfdnRzX290ZlwiXSIsInZlbmNvZGVfdGFnIjoidnRzX3ZvZF91cmxnZW4uY2xpcHMuYzIuNzIwLmJhc2VsaW5lIn0&_nc_cat=108&vs=593397427138359_793040696&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC8xRTQ3OTVDMzA2QjMxMUM4RDJEMTI1NzEzRjJCQjhBN192aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HUEVoZXg2ZmxydHFvRzBpQUN2c21lSHRBM2t1YnFfRUFBQUYVAgLIARIAKAAYABsAFQAAJqTEoObW99I%2FFQIoAkMzLBdAXEzMzMzMzRgSZGFzaF9iYXNlbGluZV8xX3YxEQB1%2Fgdl5p0BAA%3D%3D&_nc_rid=d31b48f60e&ccb=9-4&oh=00_AfOjBTnL9otf-4mdUXj4Xk0_3pqfJYF6yJ3gVE3dCM9lbA&oe=685CEF81&_nc_sid=d885a2"
    
    try:
        print(f"Testing GIF conversion for: {video_url[:100]}...")
        
        gif_bytes = client.url_to_gif(
            url=video_url,
            start_time=25,
            end_time=49,
            resize="100%",
            speed="1x", 
            fps=8,
            quality=75,
            loop="forever"
        )
        
        print(f"✅ Success! Generated GIF with {len(gif_bytes)} bytes")
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error {e.response.status_code}: {e.response.reason_phrase}")
        print(f"URL: {e.request.url}")
        
        try:
            error_response = e.response.json()
            print(f"Error details: {error_response.get('detail', 'No details available')}")
        except:
            print(f"Raw response: {e.response.text}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_instagram_gif()
import pytest
import os
from tests.fixtures.test_urls import ACTIVE_TEST_URLS, LINKEDIN_VIDEO_URLS


@pytest.mark.e2e
@pytest.mark.slow
class TestRealVideoExtraction:
    """End-to-end tests with real social media URLs."""
    
    @pytest.mark.parametrize("test_data", ACTIVE_TEST_URLS, ids=lambda d: d["description"])
    def test_extract_video_url_from_real_posts(self, test_data):
        """Test extracting video URLs from real social media posts."""
        from src.core.video import extract_video_url
        
        try:
            result = extract_video_url(test_data["url"])
            
            # Basic validations
            assert result.startswith("http"), f"URL should start with http: {result}"
            assert len(result) > 20, f"URL seems too short: {result}"
            
            # Platform-specific validations if provided
            if "expected_domain" in test_data:
                assert test_data["expected_domain"] in result, \
                    f"Expected domain {test_data['expected_domain']} not found in {result}"
            
            print(f"\n✓ Successfully extracted video URL from {test_data['description']}")
            print(f"  Source: {test_data['url']}")
            print(f"  Video: {result[:100]}...")
            
        except Exception as e:
            if not test_data.get("active", True):
                pytest.skip(f"Test URL marked as inactive: {test_data['description']}")
            else:
                pytest.fail(f"Failed to extract video from {test_data['description']}: {str(e)}")
    
    @pytest.mark.parametrize("test_data", LINKEDIN_VIDEO_URLS, ids=lambda d: d["description"])
    def test_clip_linkedin_videos(self, test_data, temp_dir):
        """Test clipping videos from LinkedIn posts."""
        if not test_data.get("active", True):
            pytest.skip("Test URL marked as inactive")
        
        from src.core.video import extract_video_url, clip_video
        
        try:
            # First extract the video URL
            video_url = extract_video_url(test_data["url"])
            print(f"\nExtracted video URL: {video_url[:100]}...")
            
            # Then clip a small portion (2 seconds)
            video_bytes = clip_video(video_url, 0.0, 2.0)
            
            # Basic validations
            assert len(video_bytes) > 1000, "Video file seems too small"
            assert video_bytes[:3] == b'\x00\x00\x00', "Not a valid MP4 file"
            
            # Optionally save for manual inspection
            if os.getenv("SAVE_TEST_VIDEOS"):
                output_path = temp_dir / f"linkedin_clip_{test_data['url'].split('/')[-2]}.mp4"
                output_path.write_bytes(video_bytes)
                print(f"  Saved test video to: {output_path}")
            
            print(f"✓ Successfully clipped video: {len(video_bytes)} bytes")
            
        except Exception as e:
            pytest.fail(f"Failed to clip LinkedIn video: {str(e)}")


@pytest.mark.e2e
@pytest.mark.slow
class TestRealVideoAPI:
    """End-to-end API tests with real URLs."""
    
    @pytest.mark.asyncio
    async def test_api_extract_linkedin_video(self, async_client):
        """Test API endpoint with real LinkedIn URL."""
        linkedin_url = LINKEDIN_VIDEO_URLS[0]["url"]
        
        response = await async_client.post(
            "/api/video/extract-url",
            json={"url": linkedin_url}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "video_url" in data
        assert data["video_url"].startswith("http")
        print(f"\nAPI extracted video URL: {data['video_url'][:100]}...")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("SKIP_SLOW_E2E") == "1",
        reason="Skipping slow E2E test"
    )
    async def test_api_clip_real_video(self, async_client):
        """Test API clipping with a real video URL."""
        # First get a video URL
        linkedin_url = LINKEDIN_VIDEO_URLS[0]["url"]
        
        extract_response = await async_client.post(
            "/api/video/extract-url",
            json={"url": linkedin_url}
        )
        
        assert extract_response.status_code == 200
        video_url = extract_response.json()["video_url"]
        
        # Then clip it
        clip_response = await async_client.post(
            "/api/video/clip",
            json={
                "url": video_url,
                "start_time": 0.0,
                "end_time": 2.0
            }
        )
        
        assert clip_response.status_code == 200
        assert clip_response.headers["content-type"] == "video/mp4"
        
        video_bytes = clip_response.content
        assert len(video_bytes) > 1000
        print(f"\nAPI clipped video: {len(video_bytes)} bytes")
"""
Test URLs for integration and E2E testing.
These are real social media URLs that contain videos.
"""

from typing import Any, Dict, List, Literal


TEST_LINK_TYPE = Dict[str, Any]

# LinkedIn video posts
LINKEDIN_VIDEO_URLS: List[TEST_LINK_TYPE] = [
    {
        "url": "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/",
        "description": "LinkedIn post with video",
        "expected_domain": "dms.licdn.com",
        "active": True,
    }
]

# X (Twitter) video posts - to be added
X_VIDEO_URLS: List[TEST_LINK_TYPE] = []

# YouTube test videos
YOUTUBE_VIDEO_URLS: List[TEST_LINK_TYPE] = [
    {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "description": "Me at the zoo - First YouTube video",
        "expected_domain": "googlevideo.com",
        "active": True,
    }
]

# All test URLs combined
ALL_TEST_URLS = LINKEDIN_VIDEO_URLS + X_VIDEO_URLS + YOUTUBE_VIDEO_URLS

# Get only active URLs
ACTIVE_TEST_URLS = [url for url in ALL_TEST_URLS if url.get("active", True)]

PLATFORM_TYPE = Literal["linkedin", "x", "twitter", "youtube"]


def get_test_urls_by_platform(platform: PLATFORM_TYPE) -> List[TEST_LINK_TYPE]:
    """Get test URLs for a specific platform."""
    platform_map = {
        "linkedin": LINKEDIN_VIDEO_URLS,
        "x": X_VIDEO_URLS,
        "twitter": X_VIDEO_URLS,
        "youtube": YOUTUBE_VIDEO_URLS,
    }
    return platform_map.get(platform.lower(), [])

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, HttpUrl
from typing import Optional

from ..core.video import extract_video_url, clip_video


router = APIRouter(prefix="/api/video", tags=["video"])


class ExtractVideoRequest(BaseModel):
    url: HttpUrl


class ExtractVideoResponse(BaseModel):
    video_url: str


class ClipVideoRequest(BaseModel):
    url: HttpUrl
    start_time: float
    end_time: float


@router.post("/extract-url", response_model=ExtractVideoResponse)
async def extract_video_url_endpoint(request: ExtractVideoRequest) -> ExtractVideoResponse:
    """
    Extract direct video URL from a social media post URL.
    
    This endpoint takes a social media post URL (from X.com, LinkedIn, etc.)
    and returns the direct URL to the video file that can be downloaded.
    """
    try:
        video_url = extract_video_url(str(request.url))
        return ExtractVideoResponse(video_url=video_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/clip")
async def clip_video_endpoint(request: ClipVideoRequest) -> Response:
    """
    Clip a video between specified timestamps and return as binary data.
    
    This endpoint downloads a video from the provided URL, clips it between
    the start and end times (in seconds), and returns the clipped video as
    binary data.
    """
    try:
        video_bytes = clip_video(
            str(request.url),
            request.start_time,
            request.end_time
        )
        
        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename=clipped_video.mp4"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
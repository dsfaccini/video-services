import traceback
import os
from fastapi import APIRouter, HTTPException, Response, Query, File, UploadFile
from pydantic import BaseModel, HttpUrl
from typing import Annotated, Literal

from ..core import video, gif


router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/extract-url")
async def extract_video_url_endpoint(
    url: HttpUrl = Query(..., description="Social media post URL"),
) -> dict[str, str]:
    """
    Extract direct video URL from a social media post URL.

    This endpoint takes a social media post URL (from X.com, LinkedIn, etc.)
    and returns the direct URL to the video file that can be downloaded.
    """
    try:
        video_url = video.extract_video_url(str(url))
        return {"video_url": video_url}
            
    except ValueError as e:
        error_detail = str(e)
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal server error: {str(e)}"
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/clip")
async def clip_video_endpoint(
    url: HttpUrl = Query(..., description="Video URL or social media post URL"),
    start_time: float = Query(..., description="Start time in seconds", ge=0),
    end_time: float = Query(..., description="End time in seconds", gt=0),
) -> Response:
    """
    Clip a video between specified timestamps and return as binary data.

    This endpoint downloads a video from the provided URL, clips it between
    the start and end times (in seconds), and returns the clipped video as
    binary data.
    """
    try:
        video_bytes = video.clip_video(str(url), start_time, end_time)

        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=clipped_video.mp4"},
        )
    except ValueError as e:
        error_detail = str(e)
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal server error: {str(e)}"
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


class VideoToGifOptions(BaseModel):
    url: HttpUrl
    #  NOTE we're keeping this obligatory for now
    start_time: float
    end_time: float
    resize: Literal["25%", "50%", "75%", "100%"] = "100%"
    speed: Literal["0.5x", "1x", "2x", "4x"] = "1x"
    fps: int = 8
    quality: int = 75
    loop: Literal["forever", "once", "none"] = "forever"

@router.get("/to-gif/from-url")
async def url_to_gif_endpoint(params: Annotated[VideoToGifOptions, Query()]
) -> Response:
    """
    Convert video from URL to GIF with clipping and specified options.

    This endpoint downloads a video from the provided URL, clips it between
    the start and end times, and converts it to GIF format with customizable
    options for resize, speed, fps, quality, and loop behavior.
    """
    try:
        video_bytes = video.clip_video(str(params.url), params.start_time, params.end_time)

        gif_bytes = gif.from_video(
            video_bytes=video_bytes,
            resize=params.resize,
            speed=params.speed,
            fps=params.fps,
            quality=params.quality,
            loop=params.loop,
        )

        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={"Content-Disposition": "attachment; filename=converted.gif"},
        )
    except ValueError as e:
        error_detail = str(e)
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal server error: {str(e)}"
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
    
@router.post("/to-gif/from-file")
async def file_to_gif(
    video: UploadFile = File(..., description="Video file to convert"),
    resize: Literal["25%", "50%", "75%", "100%"] = Query(
        "100%", description="Resize percentage"
    ),
    speed: Literal["0.5x", "1x", "2x", "4x"] = Query(
        "1x", description="Speed multiplier"
    ),
    fps: int = Query(8, description="Frames per second", ge=3, le=10),
    quality: int = Query(75, description="GIF quality", ge=0, le=100),
    loop: Literal["forever", "once", "none"] = Query(
        "forever", description="Loop behavior"
    ),
) -> Response:
    """
    Convert uploaded video file to GIF with specified options.

    This endpoint accepts a video file upload and converts it to GIF format
    with customizable options for resize, speed, fps, quality, and loop behavior.
    """
    try:
        # Read video file content
        video_bytes = await video.read()

        # Convert to GIF
        gif_bytes = gif.from_video(
            video_bytes=video_bytes,
            resize=resize,
            speed=speed,
            fps=fps,
            quality=quality,
            loop=loop,
        )

        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={
                "Content-Disposition": f"attachment; filename={video.filename.rsplit('.', 1)[0] if video.filename else 'video'}.gif"
            },
        )
    except ValueError as e:
        error_detail = str(e)
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        error_detail = f"Internal server error: {str(e)}"
        if os.getenv("DEBUG") or os.getenv("ENVIRONMENT") == "development":
            error_detail = f"{error_detail}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

from fastapi import APIRouter, HTTPException, Response, Query, File, UploadFile
from pydantic import HttpUrl
from typing import Literal
import json

from ..core.video import extract_video_url, clip_video, make_gif, url_to_gif


router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/extract-url")
async def extract_video_url_endpoint(
    url: HttpUrl = Query(..., description="Social media post URL"),
) -> Response:
    """
    Extract direct video URL from a social media post URL.

    This endpoint takes a social media post URL (from X.com, LinkedIn, etc.)
    and returns the direct URL to the video file that can be downloaded.
    """
    try:
        video_url = extract_video_url(str(url))
        return Response(
            content=json.dumps({"video_url": video_url}),
            media_type="application/json",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
        video_bytes = clip_video(str(url), start_time, end_time)

        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={"Content-Disposition": "attachment; filename=clipped_video.mp4"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/url-to-gif")
async def url_to_gif_endpoint(
    url: HttpUrl = Query(..., description="Video URL or social media post URL"),
    start_time: float = Query(..., description="Start time in seconds", ge=0),
    end_time: float = Query(..., description="End time in seconds", gt=0),
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
    Convert video from URL to GIF with clipping and specified options.

    This endpoint downloads a video from the provided URL, clips it between
    the start and end times, and converts it to GIF format with customizable
    options for resize, speed, fps, quality, and loop behavior.
    """
    try:
        gif_bytes = url_to_gif(
            source_url=str(url),
            start_time=start_time,
            end_time=end_time,
            resize=resize,
            speed=speed,
            fps=fps,
            quality=quality,
            loop=loop,
        )

        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={"Content-Disposition": "attachment; filename=converted.gif"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/make-gif")
async def make_gif_endpoint(
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
        gif_bytes = make_gif(
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

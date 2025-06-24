from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import video


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Video Services API",
        description="API for video processing atomic actions",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(video.router)

    # Root endpoint
    @app.get("/")
    async def root() -> Dict[str, Any]:
        return {
            "message": "Video Services API",
            "version": "0.1.0",
            "endpoints": {
                "extract_video_url": "/api/video/extract-url",
                "clip_video": "/api/video/clip",
                "url_to_gif": "/api/video/to-gif/from-url",
                "file_to_gif": "/api/video/to-gif/from-file",
            },
        }

    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()

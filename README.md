# Video Services API

A FastAPI server that provides atomic video processing actions using yt-dlp. Supports extracting video URLs from social media posts and clipping videos directly from social media URLs.

## Features

- **Extract Video URL**: Get direct video URLs from social media posts (LinkedIn, YouTube, X.com, etc.)
- **Clip Video**: Download and clip videos directly from social media URLs or direct video URLs
- **Atomic Operations**: Each endpoint performs a single, focused operation
- **Comprehensive Testing**: Unit, integration, and E2E tests with real social media content

## Project Structure

```
video-services/
├── src/
│   ├── app.py                 # FastAPI application setup
│   ├── core/                  # Business logic
│   │   └── video.py          # Video processing functions (yt-dlp only)
│   └── routes/               # API routes
│       └── video.py          # Video endpoints
├── tests/                     # Comprehensive test suite
│   ├── unit/                 # Fast tests with mocked dependencies
│   ├── integration/          # Tests with real yt-dlp but controlled inputs
│   ├── e2e/                  # Tests with live social media URLs
│   └── fixtures/             # Test data and utilities
├── dev.sh                    # Development helper script
├── curl.sh                   # API interaction script
├── Dockerfile                # Optimized Docker configuration with healthcheck
├── DEVELOPMENT_WORKFLOW.md   # Research-first development workflow
├── main.py                   # Application entry point
├── pyproject.toml            # Python dependencies and configuration
└── pytest.ini               # Test configuration
```

## API Endpoints

### Extract Video URL
Extract the direct video URL from a social media post:

```bash
POST /api/video/extract-url
Content-Type: application/json

{
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/"
}

Response:
{
    "video_url": "https://dms.licdn.com/playlist/vid/v2/..."
}
```

### Clip Video
Download and clip a video directly from social media URLs or video URLs:

```bash
POST /api/video/clip
Content-Type: application/json

{
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/",
    "start_time": 10.0,
    "end_time": 30.0
}

Response: video/mp4 binary data (clipped portion only)
```

**Note**: The clip endpoint accepts both social media URLs and direct video URLs, making it flexible for different use cases.

## Quick Start

### Prerequisites
- Python 3.13+
- No external dependencies required (yt-dlp handles everything internally)

### Installation

```bash
# Using uv (recommended)
uv venv
uv pip install -e "."

# Or using pip
pip install -e "."
```

### Running the Server

```bash
# Using the development script (recommended)
./dev.sh serve

# Or directly
python main.py
```

The server will start on `http://localhost:8000`

### Quick API Test

```bash
# Extract a video URL
./curl.sh extract "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/"

# Clip a video (10-30 seconds) and save to file
./curl.sh clip "https://www.linkedin.com/feed/update/urn:li:activity:7335907657188360192/" 10 30 output.mp4

# Check server health
./curl.sh health
```

## Development Scripts

### `./dev.sh` - Development Helper

```bash
./dev.sh serve          # Start development server
./dev.sh test_unit      # Run unit tests (fast, mocked)
./dev.sh test_integration # Run integration tests
./dev.sh test_e2e       # Run E2E tests with real URLs
./dev.sh test_all       # Run all tests
./dev.sh check          # Run type checking with mypy
./dev.sh lint           # Run linting (if configured)
./dev.sh install        # Install dependencies
```

### `./curl.sh` - API Interaction

```bash
./curl.sh extract <social_media_url>                    # Extract video URL
./curl.sh clip <url> <start_time> <end_time> <output>  # Clip video
./curl.sh health                                        # Health check
```

## Docker

### Build and Run

```bash
# Build the optimized image
docker build -t video-services .

# Run with healthcheck
docker run -p 8000:8000 video-services

# Check health
docker ps  # Shows health status
```

The Docker image includes:
- Multi-stage build for optimized size
- Health check endpoint monitoring
- Virtual environment isolation
- All necessary dependencies bundled

## Development

### Technology Stack

- **FastAPI**: Web framework for building APIs
- **yt-dlp**: Video URL extraction and downloading (handles all video processing)
- **Pydantic**: Data validation and settings
- **uvicorn**: ASGI server
- **pytest**: Testing framework with comprehensive test markers

### Architecture Benefits

- **Single Dependency**: yt-dlp handles both extraction and clipping
- **No External Tools**: No ffmpeg or other system dependencies required
- **Efficient Processing**: yt-dlp's native clipping avoids unnecessary downloads
- **Robust Error Handling**: Built-in support for various social media platforms

## Testing

### Test Strategy

The project uses a 3-tier testing approach:

```bash
# Unit Tests (fast, mocked dependencies)
./dev.sh test_unit

# Integration Tests (real yt-dlp, controlled inputs)  
./dev.sh test_integration

# E2E Tests (real social media URLs, internet required)
./dev.sh test_e2e
```

### Test Types

1. **Unit Tests** (`-m unit`): Fast tests with mocked dependencies
   - Business logic validation
   - Error handling and edge cases
   - No network calls or external dependencies

2. **Integration Tests** (`-m integration`): Tests with real yt-dlp
   - Video processing with test URLs
   - VCR cassettes for HTTP interaction recording
   - Controlled network resources

3. **E2E Tests** (`-m e2e`): Full end-to-end validation
   - Real social media URLs (LinkedIn, YouTube)
   - Domain validation (dms.licdn.com, googlevideo.com)
   - Internet connection required

### Test Data

Real social media URLs are maintained in `tests/fixtures/test_urls.py`:
- LinkedIn video posts with domain validation
- YouTube test videos
- Active/inactive URL management

## Health Check

```bash
GET /health

Response:
{
    "status": "healthy",
    "version": "0.1.0"
}
```

## Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `SKIP_SLOW_E2E`: Skip slow E2E tests (default: unset)
- `SAVE_TEST_VIDEOS`: Save test videos for inspection (default: unset)

## Performance Notes

- **Efficient Clipping**: yt-dlp downloads only the requested time range
- **No Intermediate Files**: Direct streaming when possible
- **Platform Optimized**: Native support for major social media platforms
- **Error Recovery**: Robust handling of platform-specific issues

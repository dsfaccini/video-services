# Configuration Guide

## Environment Variables

The Video Services API client supports configuration through environment variables. Create a `.env` file in the project root to configure the client.

### Setup

1. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```bash
   # For production
   VIDEO_API_BASE_URL=https://faccit.getalecs.com
   VIDEO_API_USERNAME=your_username
   VIDEO_API_PASSWORD=your_password
   VIDEO_API_OUTPUT_DIR=./downloads

   # For local development  
   VIDEO_API_BASE_URL=http://localhost:8000
   VIDEO_API_TIMEOUT=60.0
   ```

### Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VIDEO_API_BASE_URL` | API base URL | `http://localhost:8000` |
| `VIDEO_API_USERNAME` | Authentication username | None |
| `VIDEO_API_PASSWORD` | Authentication password | None |
| `VIDEO_API_TIMEOUT` | Request timeout in seconds | `60.0` |
| `VIDEO_API_OUTPUT_DIR` | Default directory for downloaded files | `.` |

### Usage Examples

#### Basic Usage (with .env file)
```python
from client import VideoServicesClient

# Uses configuration from .env file automatically
with VideoServicesClient() as client:
    video_url = client.extract_video_url("https://x.com/some_post")
    client.clip_video(video_url, 0, 5, save_to="clip.mp4")
```

#### Override Configuration
```python
from client import VideoServicesClient
from config import Config

# Create custom config
custom_config = Config(
    base_url="https://different-api.com",
    username="different_user",
    password="different_pass"
)

with VideoServicesClient(config=custom_config) as client:
    # Uses custom configuration
    pass
```

#### Parameter Overrides
```python
from client import VideoServicesClient

# Override specific parameters while keeping .env defaults
with VideoServicesClient(base_url="https://staging-api.com") as client:
    # Uses staging URL but keeps other .env settings
    pass
```

### Quick Functions

All quick functions also support the configuration system:

```python
from client import quick_extract, quick_clip, quick_gif

# Uses .env configuration
video_url = quick_extract("https://x.com/some_post")

# Files are saved to VIDEO_API_OUTPUT_DIR from .env
quick_clip(video_url, 0, 5, save_to="output.mp4")
quick_gif("https://x.com/some_post", 0, 3, save_to="output.gif")
```

### File Output

When using `save_to` parameters:
- **Absolute paths**: Saved exactly where specified
- **Relative paths**: Saved relative to `VIDEO_API_OUTPUT_DIR`
- **Automatic directory creation**: Parent directories are created if they don't exist

Example:
```python
# If VIDEO_API_OUTPUT_DIR=./downloads
client.clip_video(url, 0, 5, save_to="clips/video.mp4")
# Saves to: ./downloads/clips/video.mp4
```
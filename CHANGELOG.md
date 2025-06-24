# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-24

### Added
- New GIF conversion endpoints (`/api/video/url-to-gif` and `/api/video/to-gif/from-file`)
- HTTPX client utility for convenient API interaction with authentication support
- Comprehensive test suite for all endpoints including GIF functionality
- Video file upload support for GIF conversion

### Changed
- **BREAKING**: Refactored all video endpoints from POST with JSON to GET with query parameters
- All endpoints now return consistent Response objects instead of mixed return types
- Improved test output by redirecting byte information to temporary log files
- Enhanced error handling and parameter validation

### Technical
- Updated FastAPI endpoint signatures for better OpenAPI documentation
- Added comprehensive type hints and improved code quality
- Implemented proper HTTP status codes and error responses
- Added development utility scripts and examples

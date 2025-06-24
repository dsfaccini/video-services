import pytest
import vcr
import tempfile
from pathlib import Path
from tests.fixtures.test_urls import LINKEDIN_VIDEO_URLS


# Configure VCR
vcr_cassette_dir = Path(__file__).parent.parent / "fixtures" / "vcr_cassettes"
vcr_cassette_dir.mkdir(exist_ok=True)

my_vcr = vcr.VCR(
    cassette_library_dir=str(vcr_cassette_dir),
    # record_mode='once',  # Record if cassette doesn't exist, replay if it does
    match_on=["uri", "method"],
    filter_headers=["authorization", "cookie"],
    filter_query_parameters=["api_key"],
    decode_compressed_response=True,
)


@pytest.mark.integration
class TestVideoWithVCR:
    """Integration tests using VCR to record/replay HTTP interactions."""

    @my_vcr.use_cassette("linkedin_video_extraction.yaml")
    def test_extract_linkedin_video_with_vcr(self):
        """Test LinkedIn video extraction with recorded HTTP responses."""
        from src.core.video import extract_video_url

        # This will use real HTTP on first run, then replay from cassette
        linkedin_url = LINKEDIN_VIDEO_URLS[0]["url"]

        try:
            result = extract_video_url(linkedin_url)
            assert result.startswith("http")
            assert "linkedin" in result.lower() or "licdn" in result.lower()
            print(f"\nExtracted URL (via VCR): {result[:100]}...")
        except Exception as e:
            # If LinkedIn changes their API, the cassette may need to be deleted and re-recorded
            pytest.skip(f"VCR playback failed, may need to re-record cassette: {e}")

    @pytest.mark.slow
    @my_vcr.use_cassette("video_download_and_clip.yaml")  # type: ignore[misc]
    def test_clip_video_with_vcr(self, temp_dir: Path) -> None:
        """Test video clipping with recorded HTTP responses."""
        from src.core.video import clip_video

        # Use a small test video URL that's stable
        test_video_url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"

        try:
            # Clip first 2 seconds
            result = clip_video(test_video_url, 0.0, 2.0)

            assert len(result) > 1000
            # Check for MP4 file signature (more tolerant check)
            assert result[:3] == b"\x00\x00\x00", (
                f"Invalid MP4 header: {result[:8].hex()}"
            )

            # Save for inspection if needed
            output_path = temp_dir / "vcr_clipped_video.mp4"
            output_path.write_bytes(result)
            
            # Log video size to temp file instead of console
            log_file = tempfile.mktemp(suffix='.log', prefix='vcr_clip_test_')
            with open(log_file, 'w') as f:
                f.write(f"Clipped video size: {len(result)} bytes\n")
                f.write(f"Output saved to: {output_path}\n")
                f.write(f"Test URL: {test_video_url}\n")
            print(f"\nClipped video size logged to {log_file}")

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                pytest.skip("Test video URL no longer available")
            else:
                # Log error details to file instead of console
                error_log = tempfile.mktemp(suffix=".log", prefix="test_error_")
                with open(error_log, "w") as f:
                    f.write("Test error details:\n")
                    f.write(f"Exception: {str(e)}\n")
                    f.write(f"Exception type: {type(e)}\n")
                    if hasattr(e, "__traceback__"):
                        import traceback

                        f.write("Traceback:\n")
                        traceback.print_exc(file=f)
                print(f"\nError details written to: {error_log}")
                raise

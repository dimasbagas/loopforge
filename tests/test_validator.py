import pytest
from pathlib import Path
from loopforge.utils.validator import (
    ValidationError, validate_duration_positive, validate_video_extension,
    validate_youtube_url,
)


class TestValidateDuration:
    def test_valid_duration(self):
        assert validate_duration_positive(60) == 60
        assert validate_duration_positive(3600) == 3600
        assert validate_duration_positive(0.1) == 0.1

    def test_zero_duration(self):
        with pytest.raises(ValidationError):
            validate_duration_positive(0)

    def test_negative_duration(self):
        with pytest.raises(ValidationError):
            validate_duration_positive(-1)


class TestValidateVideoExtension:
    def test_valid_extensions(self):
        for ext in [".mp4", ".avi", ".mkv", ".mov", ".webm"]:
            path = Path(f"video{ext}")
            assert validate_video_extension(path) == ext

    def test_invalid_extension(self):
        with pytest.raises(ValidationError):
            validate_video_extension(Path("file.txt"))
        with pytest.raises(ValidationError):
            validate_video_extension(Path("file.pdf"))


class TestValidateYoutubeUrl:
    def test_valid_urls(self):
        valid_urls = [
            "https://www.youtube.com/watch?v=abc123",
            "https://youtu.be/abc123",
            "https://youtube.com/watch?v=abc123",
            "https://www.youtube.com/embed/abc123",
            "https://www.youtube.com/shorts/abc123",
        ]
        for url in valid_urls:
            assert validate_youtube_url(url), f"URL should be valid: {url}"

    def test_invalid_urls(self):
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/12345",
            "not-a-url",
            "",
            "https://www.youtube.com/",
        ]
        for url in invalid_urls:
            assert not validate_youtube_url(url), f"URL should be invalid: {url}"

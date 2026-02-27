"""Tests for the YouTube transcript extractor module."""

import pytest

from youtube_learning_extractor.extractor import extract_video_id


class TestExtractVideoId:
    def test_standard_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLtest"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_plain_video_id(self):
        assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_plain_id_with_whitespace(self):
        assert extract_video_id("  dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extract_video_id("https://example.com/not-youtube")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            extract_video_id("")

    def test_no_scheme_youtube_url(self):
        # Without scheme, urlparse puts it in the path — should raise
        with pytest.raises(ValueError):
            extract_video_id("www.youtube.com/watch?v=dQw4w9WgXcQ")

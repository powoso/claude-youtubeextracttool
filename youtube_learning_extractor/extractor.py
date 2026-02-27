"""YouTube transcript extraction module."""

from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract the video ID from various YouTube URL formats.

    Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/watch?v=VIDEO_ID&t=123
        - Plain video IDs (11 characters)
    """
    url = url.strip()

    # Plain video ID (11 alphanumeric + hyphens/underscores)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    parsed = urlparse(url)

    # youtu.be short links
    if parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id

    # Standard youtube.com URLs
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

    raise ValueError(
        f"Could not extract video ID from: {url}\n"
        "Supported formats: YouTube URL or 11-character video ID"
    )


def fetch_transcript(video_id: str, languages: tuple[str, ...] = ("en",)) -> str:
    """Fetch the transcript for a YouTube video and return as plain text."""
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=languages)
    return " ".join(snippet.text for snippet in transcript.snippets)


def get_transcript(url: str) -> tuple[str, str]:
    """High-level: extract video ID and fetch transcript.

    Returns (video_id, transcript_text).
    """
    video_id = extract_video_id(url)
    transcript_text = fetch_transcript(video_id)
    return video_id, transcript_text

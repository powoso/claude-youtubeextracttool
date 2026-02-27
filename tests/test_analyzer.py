"""Tests for the analyzer module (uses mocked Anthropic client)."""

import json
from unittest.mock import patch, MagicMock

from youtube_learning_extractor.analyzer import analyze_transcript
from youtube_learning_extractor.models import VideoAnalysis


MOCK_RESPONSE = json.dumps({
    "summary": "This video covers the fundamentals of Python programming.",
    "key_takeaways": [
        "Python is dynamically typed",
        "Lists are mutable sequences",
        "Functions are first-class objects",
    ],
    "actionable_insights": [
        "Practice with small scripts daily",
        "Read the official documentation",
    ],
    "flashcards": [
        {"question": "Is Python dynamically typed?", "answer": "Yes"},
        {"question": "Are lists mutable?", "answer": "Yes, lists are mutable"},
    ],
})


def _mock_anthropic_response(text: str) -> MagicMock:
    message = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    message.content = [content_block]
    return message


class TestAnalyzeTranscript:
    @patch("youtube_learning_extractor.analyzer.anthropic.Anthropic")
    def test_returns_video_analysis(self, mock_cls):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_anthropic_response(MOCK_RESPONSE)

        result = analyze_transcript(
            url="https://www.youtube.com/watch?v=test1234567",
            video_id="test1234567",
            title="Python Basics",
            transcript="This is a sample transcript about Python programming.",
        )

        assert isinstance(result, VideoAnalysis)
        assert result.video_id == "test1234567"
        assert result.title == "Python Basics"
        assert "Python" in result.summary
        assert len(result.key_takeaways) == 3
        assert len(result.actionable_insights) == 2
        assert len(result.flashcards) == 2

    @patch("youtube_learning_extractor.analyzer.anthropic.Anthropic")
    def test_handles_markdown_fenced_response(self, mock_cls):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        fenced = f"```json\n{MOCK_RESPONSE}\n```"
        mock_client.messages.create.return_value = _mock_anthropic_response(fenced)

        result = analyze_transcript(
            url="https://youtu.be/test1234567",
            video_id="test1234567",
            title="Test",
            transcript="Transcript text.",
        )
        assert isinstance(result, VideoAnalysis)
        assert len(result.flashcards) == 2

    @patch("youtube_learning_extractor.analyzer.anthropic.Anthropic")
    def test_truncates_long_transcripts(self, mock_cls):
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_anthropic_response(MOCK_RESPONSE)

        long_transcript = "word " * 50_000  # 250k chars
        analyze_transcript(
            url="https://youtu.be/test1234567",
            video_id="test1234567",
            title="Long Video",
            transcript=long_transcript,
        )

        # Verify the transcript sent to Claude was truncated
        call_args = mock_client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        # The truncated transcript should be shorter than the original
        assert len(user_msg) < len(long_transcript)

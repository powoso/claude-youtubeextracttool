"""Tests for data models."""

import json

from youtube_learning_extractor.models import Flashcard, VideoAnalysis


def _make_analysis(**overrides) -> VideoAnalysis:
    defaults = dict(
        video_id="abc123xyz00",
        title="Test Video",
        url="https://www.youtube.com/watch?v=abc123xyz00",
        summary="A test summary.",
        key_takeaways=["Takeaway 1", "Takeaway 2"],
        actionable_insights=["Insight 1"],
        flashcards=[Flashcard(question="Q1?", answer="A1")],
        transcript_length=5000,
        created_at="2025-01-01T00:00:00",
    )
    defaults.update(overrides)
    return VideoAnalysis(**defaults)


class TestVideoAnalysis:
    def test_to_dict_roundtrip(self):
        analysis = _make_analysis()
        d = analysis.to_dict()
        restored = VideoAnalysis.from_dict(d)
        assert restored.video_id == analysis.video_id
        assert restored.title == analysis.title
        assert restored.summary == analysis.summary
        assert len(restored.flashcards) == 1
        assert restored.flashcards[0].question == "Q1?"

    def test_to_json(self):
        analysis = _make_analysis()
        j = analysis.to_json()
        parsed = json.loads(j)
        assert parsed["video_id"] == "abc123xyz00"
        assert isinstance(parsed["flashcards"], list)

    def test_format_display_contains_sections(self):
        analysis = _make_analysis()
        display = analysis.format_display()
        assert "## Summary" in display
        assert "## Key Takeaways" in display
        assert "## Actionable Insights" in display
        assert "## Flashcards" in display
        assert "Q1?" in display
        assert "A1" in display

    def test_from_dict_with_multiple_flashcards(self):
        data = {
            "video_id": "test123test",
            "title": "Multi-card",
            "url": "https://youtu.be/test123test",
            "summary": "Summary",
            "key_takeaways": ["T1"],
            "actionable_insights": ["I1"],
            "flashcards": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
            ],
            "transcript_length": 100,
        }
        analysis = VideoAnalysis.from_dict(data)
        assert len(analysis.flashcards) == 2
        assert analysis.flashcards[1].question == "Q2"

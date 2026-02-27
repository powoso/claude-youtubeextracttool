"""Tests for the personal library module."""

import os
import tempfile

import pytest

from youtube_learning_extractor.library import Library
from youtube_learning_extractor.models import Flashcard, VideoAnalysis


def _make_analysis(video_id="test_vid_001", title="Test Video", **overrides) -> VideoAnalysis:
    defaults = dict(
        video_id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        summary="This is a test summary about machine learning basics.",
        key_takeaways=["Neural networks learn from data", "Backpropagation is key"],
        actionable_insights=["Start with simple models first"],
        flashcards=[Flashcard(question="What is backprop?", answer="Gradient-based learning")],
        transcript_length=3000,
        created_at="2025-06-01T12:00:00",
    )
    defaults.update(overrides)
    return VideoAnalysis(**defaults)


@pytest.fixture()
def lib():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    library = Library(db_path=path)
    yield library
    library.close()
    os.unlink(path)


class TestLibrary:
    def test_save_and_get(self, lib: Library):
        analysis = _make_analysis()
        lib.save(analysis)
        retrieved = lib.get("test_vid_001")
        assert retrieved is not None
        assert retrieved.title == "Test Video"
        assert retrieved.summary == analysis.summary
        assert len(retrieved.flashcards) == 1

    def test_get_nonexistent(self, lib: Library):
        assert lib.get("nonexistent") is None

    def test_list_all_empty(self, lib: Library):
        assert lib.list_all() == []

    def test_list_all_ordered(self, lib: Library):
        lib.save(_make_analysis(video_id="vid_001_aaa", created_at="2025-01-01T00:00:00"))
        lib.save(_make_analysis(video_id="vid_002_bbb", created_at="2025-06-01T00:00:00"))
        results = lib.list_all()
        assert len(results) == 2
        # Most recent first
        assert results[0].video_id == "vid_002_bbb"

    def test_search(self, lib: Library):
        lib.save(_make_analysis(video_id="ml_vid_0001", title="Machine Learning 101",
                                summary="Introduction to machine learning concepts."))
        lib.save(_make_analysis(video_id="cook_vid_01", title="Cooking Pasta",
                                summary="How to cook perfect pasta at home."))
        results = lib.search("machine learning")
        assert len(results) == 1
        assert results[0].video_id == "ml_vid_0001"

    def test_search_no_results(self, lib: Library):
        lib.save(_make_analysis())
        results = lib.search("quantum physics")
        assert results == []

    def test_delete(self, lib: Library):
        lib.save(_make_analysis())
        assert lib.delete("test_vid_001") is True
        assert lib.get("test_vid_001") is None

    def test_delete_nonexistent(self, lib: Library):
        assert lib.delete("nonexistent") is False

    def test_save_replaces_existing(self, lib: Library):
        lib.save(_make_analysis(title="Original Title"))
        lib.save(_make_analysis(title="Updated Title"))
        retrieved = lib.get("test_vid_001")
        assert retrieved.title == "Updated Title"

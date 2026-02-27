"""Tests for the Flask web application."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from youtube_learning_extractor.models import Flashcard, VideoAnalysis
from youtube_learning_extractor.webapp import app


def _make_analysis(video_id="testvid0001", title="Test Video") -> VideoAnalysis:
    return VideoAnalysis(
        video_id=video_id,
        title=title,
        url=f"https://www.youtube.com/watch?v={video_id}",
        summary="A great summary of the test video.",
        key_takeaways=["Takeaway one", "Takeaway two"],
        actionable_insights=["Do this first"],
        flashcards=[Flashcard(question="What is X?", answer="X is Y")],
        transcript_length=5000,
        created_at="2025-06-01T12:00:00",
    )


@pytest.fixture()
def client(tmp_path):
    db_path = str(tmp_path / "test.db")
    with patch("youtube_learning_extractor.webapp._get_library") as mock_lib_fn:
        from youtube_learning_extractor.library import Library

        lib = Library(db_path=db_path)
        mock_lib_fn.return_value = lib
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c, lib
        lib.close()


class TestPages:
    def test_index(self, client):
        c, _ = client
        resp = c.get("/")
        assert resp.status_code == 200
        assert b"YouTube" in resp.data

    def test_library_empty(self, client):
        c, _ = client
        resp = c.get("/library")
        assert resp.status_code == 200
        assert b"empty" in resp.data.lower()

    def test_library_with_video(self, client):
        c, lib = client
        lib.save(_make_analysis())
        resp = c.get("/library")
        assert resp.status_code == 200
        assert b"Test Video" in resp.data

    def test_library_search(self, client):
        c, lib = client
        lib.save(_make_analysis(title="Machine Learning Intro"))
        resp = c.get("/library?q=machine")
        assert resp.status_code == 200
        assert b"Machine Learning" in resp.data

    def test_result_page(self, client):
        c, lib = client
        lib.save(_make_analysis())
        resp = c.get("/result/testvid0001")
        assert resp.status_code == 200
        assert b"Test Video" in resp.data
        assert b"Summary" in resp.data

    def test_result_not_found(self, client):
        c, _ = client
        resp = c.get("/result/nonexistent")
        assert resp.status_code == 404

    def test_flashcards_page(self, client):
        c, lib = client
        lib.save(_make_analysis())
        resp = c.get("/flashcards/testvid0001")
        assert resp.status_code == 200
        assert b"What is X?" in resp.data


class TestAPI:
    def test_extract_missing_url(self, client):
        c, _ = client
        resp = c.post("/api/extract", json={})
        assert resp.status_code == 400

    def test_extract_starts_task(self, client):
        c, _ = client
        with patch("youtube_learning_extractor.webapp._run_extraction"):
            resp = c.post("/api/extract", json={"url": "https://www.youtube.com/watch?v=test1234567"})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "task_id" in data

    def test_status_unknown_task(self, client):
        c, _ = client
        resp = c.get("/api/status/99999")
        assert resp.status_code == 404

    def test_delete_api(self, client):
        c, lib = client
        lib.save(_make_analysis())
        resp = c.delete("/api/videos/testvid0001")
        assert resp.status_code == 200
        assert json.loads(resp.data)["deleted"] is True

    def test_delete_api_not_found(self, client):
        c, _ = client
        resp = c.delete("/api/videos/nonexistent")
        assert resp.status_code == 404

    def test_export_api(self, client):
        c, lib = client
        lib.save(_make_analysis())
        resp = c.get("/api/videos/testvid0001/export")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["video_id"] == "testvid0001"

    def test_export_not_found(self, client):
        c, _ = client
        resp = c.get("/api/videos/nonexistent/export")
        assert resp.status_code == 404

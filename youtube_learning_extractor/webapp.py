"""Flask web application for YouTube Learning Extractor."""

from __future__ import annotations

import os
import threading

from flask import Flask, render_template, request, jsonify, redirect, url_for

from .extractor import get_transcript
from .analyzer import analyze_transcript
from .library import Library

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "yt-learn-dev-key")

# In-flight extraction tasks: task_id -> {"status": ..., "result": ..., "error": ...}
_tasks: dict[str, dict] = {}
_task_lock = threading.Lock()
_task_counter = 0


def _get_library() -> Library:
    return Library()


def _run_extraction(task_id: str, url: str, title: str | None) -> None:
    """Run transcript extraction + analysis in a background thread."""
    try:
        with _task_lock:
            _tasks[task_id]["status"] = "fetching"

        video_id, transcript = get_transcript(url)
        if title is None or title.strip() == "":
            title = f"YouTube Video ({video_id})"

        with _task_lock:
            _tasks[task_id]["status"] = "analyzing"

        analysis = analyze_transcript(
            url=url, video_id=video_id, title=title, transcript=transcript
        )

        lib = _get_library()
        lib.save(analysis)
        lib.close()

        with _task_lock:
            _tasks[task_id]["status"] = "done"
            _tasks[task_id]["video_id"] = video_id

    except Exception as e:
        with _task_lock:
            _tasks[task_id]["status"] = "error"
            _tasks[task_id]["error"] = str(e)


# ── Pages ──────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/result/<video_id>")
def result(video_id: str):
    lib = _get_library()
    analysis = lib.get(video_id)
    lib.close()
    if analysis is None:
        return render_template("404.html", message=f"Video {video_id} not found"), 404
    return render_template("result.html", v=analysis)


@app.route("/library")
def library():
    q = request.args.get("q", "").strip()
    lib = _get_library()
    if q:
        videos = lib.search(q)
    else:
        videos = lib.list_all()
    lib.close()
    return render_template("library.html", videos=videos, query=q)


@app.route("/flashcards/<video_id>")
def flashcards(video_id: str):
    lib = _get_library()
    analysis = lib.get(video_id)
    lib.close()
    if analysis is None:
        return render_template("404.html", message=f"Video {video_id} not found"), 404
    return render_template("flashcards.html", v=analysis)


# ── API ────────────────────────────────────────────────────────────────────


@app.post("/api/extract")
def api_extract():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    title = data.get("title", "").strip() or None

    if not url:
        return jsonify({"error": "URL is required"}), 400

    global _task_counter
    with _task_lock:
        _task_counter += 1
        task_id = str(_task_counter)
        _tasks[task_id] = {"status": "queued"}

    t = threading.Thread(target=_run_extraction, args=(task_id, url, title), daemon=True)
    t.start()

    return jsonify({"task_id": task_id})


@app.get("/api/status/<task_id>")
def api_status(task_id: str):
    with _task_lock:
        task = _tasks.get(task_id)
    if task is None:
        return jsonify({"error": "Unknown task"}), 404
    return jsonify(task)


@app.delete("/api/videos/<video_id>")
def api_delete(video_id: str):
    lib = _get_library()
    deleted = lib.delete(video_id)
    lib.close()
    if deleted:
        return jsonify({"deleted": True})
    return jsonify({"error": "Not found"}), 404


@app.get("/api/videos/<video_id>/export")
def api_export(video_id: str):
    lib = _get_library()
    analysis = lib.get(video_id)
    lib.close()
    if analysis is None:
        return jsonify({"error": "Not found"}), 404
    return app.response_class(
        analysis.to_json(),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={video_id}.json"},
    )


# ── Entry point ────────────────────────────────────────────────────────────


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    app.run(host=host, port=port, debug=debug)

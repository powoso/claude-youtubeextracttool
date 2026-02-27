"""Claude AI analysis module — generates structured learning materials from transcripts."""

from __future__ import annotations

import json

import anthropic

from .models import VideoAnalysis, Flashcard

SYSTEM_PROMPT = """\
You are an expert learning assistant. You analyze video transcripts and extract \
structured educational content. Always respond with valid JSON matching the exact \
schema requested. Be concise but thorough."""

USER_PROMPT_TEMPLATE = """\
Analyze the following YouTube video transcript and produce structured learning materials.

Video URL: {url}
Video Title: {title}

Transcript:
{transcript}

Return a JSON object with exactly these fields:
{{
  "summary": "A clear, well-structured summary of the video content (2-4 paragraphs)",
  "key_takeaways": ["List of 5-8 key takeaways — the most important points from the video"],
  "actionable_insights": ["List of 3-6 actionable insights — concrete steps the viewer can apply"],
  "flashcards": [
    {{"question": "A question testing understanding of a key concept", "answer": "The answer"}}
  ]
}}

Generate 5-10 flashcards covering the most important concepts. \
Make questions specific and answers concise but complete.

Return ONLY the JSON object, no markdown fences or extra text."""

MAX_TRANSCRIPT_CHARS = 100_000


def analyze_transcript(
    url: str,
    video_id: str,
    title: str,
    transcript: str,
    model: str = "claude-sonnet-4-20250514",
) -> VideoAnalysis:
    """Send transcript to Claude and return structured analysis."""
    # Truncate very long transcripts to stay within token limits
    truncated = transcript[:MAX_TRANSCRIPT_CHARS]

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    url=url, title=title, transcript=truncated
                ),
            }
        ],
    )

    response_text = message.content[0].text

    # Parse the JSON response, stripping markdown fences if present
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[: cleaned.rfind("```")]
    data = json.loads(cleaned)

    flashcards = [Flashcard(**fc) for fc in data.get("flashcards", [])]

    return VideoAnalysis(
        video_id=video_id,
        title=title,
        url=url,
        summary=data["summary"],
        key_takeaways=data["key_takeaways"],
        actionable_insights=data["actionable_insights"],
        flashcards=flashcards,
        transcript_length=len(transcript),
    )

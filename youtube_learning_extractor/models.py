"""Data models for YouTube Learning Extractor."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Flashcard:
    question: str
    answer: str


@dataclass
class VideoAnalysis:
    video_id: str
    title: str
    url: str
    summary: str
    key_takeaways: list[str]
    actionable_insights: list[str]
    flashcards: list[Flashcard]
    transcript_length: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> VideoAnalysis:
        flashcards = [Flashcard(**fc) for fc in data.get("flashcards", [])]
        return cls(
            video_id=data["video_id"],
            title=data["title"],
            url=data["url"],
            summary=data["summary"],
            key_takeaways=data["key_takeaways"],
            actionable_insights=data["actionable_insights"],
            flashcards=flashcards,
            transcript_length=data["transcript_length"],
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )

    def format_display(self) -> str:
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  {self.title}")
        lines.append(f"  {self.url}")
        lines.append(f"{'=' * 60}")

        lines.append(f"\n## Summary\n")
        lines.append(self.summary)

        lines.append(f"\n## Key Takeaways\n")
        for i, takeaway in enumerate(self.key_takeaways, 1):
            lines.append(f"  {i}. {takeaway}")

        lines.append(f"\n## Actionable Insights\n")
        for i, insight in enumerate(self.actionable_insights, 1):
            lines.append(f"  {i}. {insight}")

        lines.append(f"\n## Flashcards ({len(self.flashcards)} cards)\n")
        for i, card in enumerate(self.flashcards, 1):
            lines.append(f"  Card {i}:")
            lines.append(f"    Q: {card.question}")
            lines.append(f"    A: {card.answer}")
            lines.append("")

        lines.append(f"---")
        lines.append(f"Transcript length: {self.transcript_length:,} characters")
        lines.append(f"Analyzed: {self.created_at}")
        return "\n".join(lines)

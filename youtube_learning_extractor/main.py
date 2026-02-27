"""CLI entry point for YouTube Learning Extractor."""

from __future__ import annotations

import click

from .extractor import extract_video_id, get_transcript
from .analyzer import analyze_transcript
from .library import Library


@click.group()
def cli() -> None:
    """YouTube Learning Extractor — Turn YouTube videos into structured study materials."""


@cli.command()
@click.argument("url")
@click.option("--title", "-t", default=None, help="Video title (auto-detected if omitted).")
@click.option("--model", "-m", default="claude-sonnet-4-20250514", help="Claude model to use.")
@click.option("--no-save", is_flag=True, help="Don't save to the library.")
def extract(url: str, title: str | None, model: str, no_save: bool) -> None:
    """Extract learning materials from a YouTube video URL."""
    click.echo("Fetching transcript...")
    try:
        video_id, transcript = get_transcript(url)
    except Exception as e:
        raise click.ClickException(f"Failed to fetch transcript: {e}")

    if title is None:
        title = f"YouTube Video ({video_id})"

    click.echo(f"Transcript fetched ({len(transcript):,} chars). Analyzing with Claude...")

    try:
        analysis = analyze_transcript(
            url=url, video_id=video_id, title=title, transcript=transcript, model=model
        )
    except Exception as e:
        raise click.ClickException(f"Analysis failed: {e}")

    click.echo(analysis.format_display())

    if not no_save:
        lib = Library()
        lib.save(analysis)
        lib.close()
        click.echo(f"\nSaved to library. View again with: yt-learn show {video_id}")


@cli.command("list")
def list_videos() -> None:
    """List all videos in your library."""
    lib = Library()
    videos = lib.list_all()
    lib.close()

    if not videos:
        click.echo("Your library is empty. Extract a video with: yt-learn extract <URL>")
        return

    click.echo(f"Your library ({len(videos)} videos):\n")
    for v in videos:
        click.echo(f"  [{v.video_id}]  {v.title}")
        click.echo(f"              {v.url}")
        click.echo(f"              {len(v.flashcards)} flashcards | {v.created_at[:10]}")
        click.echo()


@cli.command()
@click.argument("video_id")
def show(video_id: str) -> None:
    """Show saved analysis for a video by its ID."""
    lib = Library()
    analysis = lib.get(video_id)
    lib.close()

    if analysis is None:
        raise click.ClickException(
            f"Video '{video_id}' not found in library. Run `yt-learn list` to see saved videos."
        )

    click.echo(analysis.format_display())


@cli.command()
@click.argument("query")
def search(query: str) -> None:
    """Search your library by keyword."""
    lib = Library()
    results = lib.search(query)
    lib.close()

    if not results:
        click.echo(f"No results for: {query}")
        return

    click.echo(f"Found {len(results)} result(s) for '{query}':\n")
    for v in results:
        click.echo(f"  [{v.video_id}]  {v.title}")
        click.echo(f"              {v.url}")
        click.echo()


@cli.command()
@click.argument("video_id")
def flashcards(video_id: str) -> None:
    """Review flashcards for a saved video (interactive)."""
    lib = Library()
    analysis = lib.get(video_id)
    lib.close()

    if analysis is None:
        raise click.ClickException(f"Video '{video_id}' not found in library.")

    if not analysis.flashcards:
        click.echo("No flashcards available for this video.")
        return

    click.echo(f"Flashcards for: {analysis.title}")
    click.echo(f"({len(analysis.flashcards)} cards — press Enter to reveal answer, 'q' to quit)\n")

    for i, card in enumerate(analysis.flashcards, 1):
        click.echo(f"Card {i}/{len(analysis.flashcards)}")
        click.echo(f"  Q: {card.question}")
        resp = click.prompt("", prompt_suffix="  [Enter to reveal, q to quit] ", default="", show_default=False)
        if resp.lower() == "q":
            break
        click.echo(f"  A: {card.answer}\n")


@cli.command()
@click.argument("video_id")
@click.confirmation_option(prompt="Are you sure you want to delete this entry?")
def delete(video_id: str) -> None:
    """Delete a video from your library."""
    lib = Library()
    deleted = lib.delete(video_id)
    lib.close()

    if deleted:
        click.echo(f"Deleted {video_id} from library.")
    else:
        click.echo(f"Video '{video_id}' not found in library.")


@cli.command()
@click.argument("video_id")
@click.argument("output", type=click.Path())
def export(video_id: str, output: str) -> None:
    """Export a video analysis to a JSON file."""
    lib = Library()
    analysis = lib.get(video_id)
    lib.close()

    if analysis is None:
        raise click.ClickException(f"Video '{video_id}' not found in library.")

    with open(output, "w") as f:
        f.write(analysis.to_json())
    click.echo(f"Exported to {output}")


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", "-p", default=5000, type=int, help="Port to listen on.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
def web(host: str, port: int, debug: bool) -> None:
    """Launch the web interface."""
    from .webapp import run_server

    click.echo(f"Starting YT Learn web app at http://{host}:{port}")
    run_server(host=host, port=port, debug=debug)


if __name__ == "__main__":
    cli()

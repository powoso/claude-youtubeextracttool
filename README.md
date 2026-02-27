# YouTube Learning Extractor

Turn any YouTube video into structured study materials — powered by Claude AI.

Paste a YouTube URL and get:
- **Structured summary** of the video content
- **Key takeaways** — the most important points
- **Actionable insights** — concrete steps you can apply
- **Auto-generated flashcards** with interactive study mode

Everything saves to a personal library with full-text search.

## Install on macOS

### Prerequisites

- **Python 3.10+** — check with `python3 --version`
- **An Anthropic API key** — get one at https://console.anthropic.com

### Step-by-step

1. **Install Python** (if you don't have it):

   ```bash
   brew install python@3.12
   ```

2. **Clone the repository:**

   ```bash
   git clone https://github.com/powoso/claude-youtubeextracttool.git
   cd claude-youtubeextracttool
   ```

3. **Create a virtual environment and install:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

4. **Set your Anthropic API key:**

   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

   To persist it, add the line above to your `~/.zshrc` (or `~/.bash_profile`):

   ```bash
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
   ```

## Usage

### Web App (recommended)

Launch the web interface:

```bash
yt-learn web
```

Then open **http://127.0.0.1:5000** in your browser.

The web app gives you:
- A clean URL input with real-time processing status
- Tabbed results view (Summary / Takeaways / Insights / Flashcards)
- Interactive flashcard study mode with flip cards and keyboard shortcuts
- A searchable personal library
- JSON export

### CLI

You can also use the command-line interface:

```bash
# Extract learning materials from a video
yt-learn extract "https://www.youtube.com/watch?v=VIDEO_ID" -t "Video Title"

# List your saved videos
yt-learn list

# Search your library
yt-learn search "machine learning"

# View a saved analysis
yt-learn show VIDEO_ID

# Interactive flashcard review
yt-learn flashcards VIDEO_ID

# Export to JSON
yt-learn export VIDEO_ID output.json

# Delete a video
yt-learn delete VIDEO_ID
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

## How It Works

1. **Transcript extraction** — Uses `youtube-transcript-api` to pull the video transcript directly from YouTube (no API key needed for this part)
2. **AI analysis** — Sends the transcript to Claude, which returns structured JSON with summary, takeaways, insights, and flashcards
3. **Persistence** — Saves results to a local SQLite database (`~/.yt_learn_library.db`) with FTS5 full-text search
4. **Web UI** — Flask serves a Tailwind CSS frontend with async extraction, tabbed views, and an interactive flashcard study mode

# markdown-documenter

A PyQt6 desktop app that converts YouTube transcripts and web articles into structured, Obsidian-ready Markdown files — with an optional AI formatting pass and a built-in Ollama chat interface.

---

## Features

### Converter tab

- **YouTube extraction** — fetches video metadata (title, channel, publish date, description) via yt-dlp and the full transcript via youtube-transcript-api. Outputs YAML frontmatter + a clean transcript body.
- **Web article extraction** — fetches and parses any article URL via trafilatura, preserving structure and metadata.
- **Output modes** — choose per-conversion:
  - `Raw only (Stage 1)` — saves extracted markdown to `output/.../raw/`
  - `Formatted only (Stage 2)` — runs the doc-formatter Ollama model to restructure the content, saves to `output/.../formatted/`
  - `Both` — saves a raw copy and a formatted copy
- **Subfolder routing** — optionally nest output under a named subfolder (e.g. `AI/videos` → `output/AI/videos/raw/`)
- **Queue** — add multiple URLs and convert them in one pass
- **Output file manager** — browse, rename, move (drag-and-drop), delete files and folders. Double-click any file to open it in the preview panel.
- **Post-process existing files** — right-click any `.md` file in the Output Files tab and select `Format with doc-formatter` to run a Stage 2 pass on files converted without it. Files in `raw/` are saved to the sibling `formatted/` directory; files elsewhere get a `formatted/` subfolder created next to them.

### Preview / Edit panel

- Rendered Markdown preview (HTML via the `markdown` library, dark/light CSS aware)
- Toggle edit mode to edit the raw Markdown directly
- Save (`Ctrl+S`) or Save As; dirty-state indicator in the title
- Copy to clipboard

### Chat tab

- Conversational interface backed by any locally running Ollama model
- Full streaming output token-by-token
- Model picker — refreshes from Ollama on demand and on startup
- Session history sent on each turn; Clear Chat to reset
- Enter to send, Stop to cancel mid-stream

---

## Output structure

```
output/
  raw/                  ← Stage 1 extraction (no subfolder)
  formatted/            ← Stage 2 doc-formatter output (no subfolder)
  AI/
    videos/
      raw/              ← Stage 1 (AI/videos subfolder)
      formatted/        ← Stage 2 (AI/videos subfolder)
```

Each file includes YAML frontmatter:
```yaml
---
title: "..."
source: "https://..."
type: youtube-transcript   # or web-article
channel: "..."             # YouTube only
author: "..."              # web articles
date_published: "YYYY-MM-DD"
date_fetched: "YYYY-MM-DD"
tags: []
---
```

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally (optional — converter works without it; Stage 2 and Chat require it)
- The `doc-formatter` model built from [ollama-configs](https://github.com/irdickinson/ollama-configs) (for Stage 2)

### Python dependencies

```
pip install -r requirements.txt
```

Key packages: `PyQt6`, `yt-dlp`, `youtube-transcript-api`, `trafilatura`, `ollama`, `markdown`

---

## Running

```powershell
cd src
python main.py
```

Or from the repo root if `src/` is on `PYTHONPATH`.

---

## Roadmap

- **Packaging** — PyInstaller exe + Windows installer so Ollama and Python don't need to be separately installed
- **YouTube chapter support** — use chapter markers as section headers instead of fixed word-count chunking
- **Chat context injection** — automatically include the currently open document as context when starting a chat session
- **MCP integration** — give the research-assistant model tool access to the full Obsidian vault via a local MCP server
- **Batch re-formatting** — select multiple files in the output tree and run Stage 2 on all at once

import re
from datetime import date

from core.youtube import YouTubeResult
from core.web import WebResult


def format_youtube(result: YouTubeResult) -> str:
    frontmatter = (
        f'---\n'
        f'title: "{_esc(result.title)}"\n'
        f'source: "{result.url}"\n'
        f'type: youtube-transcript\n'
        f'channel: "{_esc(result.channel)}"\n'
        f'date_published: "{_yt_date(result.date_published)}"\n'
        f'date_fetched: "{date.today().isoformat()}"\n'
        f'tags: []\n'
        f'---\n\n'
    )
    body = f"# {result.title}\n\n"
    if result.description:
        snippet = result.description[:300]
        if len(result.description) > 300:
            snippet += "…"
        body += f"> {snippet}\n\n"
    body += "## Transcript\n\n"
    body += result.transcript
    return frontmatter + body


def format_web(result: WebResult) -> str:
    frontmatter = (
        f'---\n'
        f'title: "{_esc(result.title)}"\n'
        f'source: "{result.url}"\n'
        f'type: article\n'
        f'author: "{_esc(result.author)}"\n'
        f'date_published: "{result.date_published}"\n'
        f'date_fetched: "{date.today().isoformat()}"\n'
        f'tags: []\n'
        f'---\n\n'
    )
    body = f"# {result.title}\n\n"
    body += result.text
    return frontmatter + body


def safe_filename(title: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\n\r]', "-", title).strip(" -")
    name = re.sub(r"\s+", " ", name)
    return name[:100] + ".md"


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _yt_date(raw: str) -> str:
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return raw

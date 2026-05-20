import re
from dataclasses import dataclass

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi


@dataclass
class YouTubeResult:
    title: str
    channel: str
    url: str
    date_published: str
    description: str
    transcript: str


def extract_youtube(url: str) -> YouTubeResult:
    video_id = _extract_video_id(url)
    meta = _fetch_metadata(url)
    transcript = _fetch_transcript(video_id)
    return YouTubeResult(
        title=meta.get("title") or "Untitled",
        channel=meta.get("uploader") or "",
        url=url,
        date_published=meta.get("upload_date") or "",
        description=meta.get("description") or "",
        transcript=transcript,
    )


def _extract_video_id(url: str) -> str:
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    raise ValueError(f"Cannot extract video ID from: {url}")


def _fetch_metadata(url: str) -> dict:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info or {}


def _fetch_transcript(video_id: str) -> str:
    entries = YouTubeTranscriptApi.get_transcript(video_id)
    raw = " ".join(e["text"] for e in entries)
    # Strip auto-generated bracketed annotations like [Music], [Applause]
    raw = re.sub(r"\[.*?\]", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    # Break into ~100-word paragraphs for readability
    words = raw.split()
    chunks = [" ".join(words[i : i + 100]) for i in range(0, len(words), 100)]
    return "\n\n".join(chunks)

from dataclasses import dataclass

import trafilatura


@dataclass
class WebResult:
    title: str
    author: str
    url: str
    date_published: str
    text: str


def extract_web(url: str) -> WebResult:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Could not fetch URL: {url}")

    text = trafilatura.extract(
        downloaded,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
        favor_precision=True,
        url=url,
    )
    if not text:
        raise ValueError(f"No extractable content at: {url}")

    meta = trafilatura.extract_metadata(downloaded, default_url=url)

    return WebResult(
        title=(meta.title if meta and meta.title else "Untitled"),
        author=(meta.author if meta and meta.author else ""),
        url=url,
        date_published=(meta.date if meta and meta.date else ""),
        text=text,
    )

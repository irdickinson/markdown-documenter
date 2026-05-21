import ollama

_MODEL = "doc-formatter"


def doc_formatter_available() -> bool:
    try:
        models = ollama.list()
        return any(m.model.startswith(_MODEL) for m in models.models)
    except Exception:
        return False


def reformat_with_doc_formatter(content: str) -> str:
    # Strip YAML frontmatter before sending — doc-formatter must not regenerate it
    body = _strip_frontmatter(content)
    response = ollama.chat(
        model=_MODEL,
        messages=[{"role": "user", "content": body}],
        stream=False,
    )
    reformatted_body = response.message.content.strip()
    # Re-attach the original frontmatter
    frontmatter = _extract_frontmatter(content)
    if frontmatter:
        return frontmatter + "\n\n" + reformatted_body
    return reformatted_body


def _extract_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return ""
    end = content.find("\n---", 3)
    if end == -1:
        return ""
    return content[: end + 4]


def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    end = content.find("\n---", 3)
    if end == -1:
        return content
    return content[end + 4 :].lstrip("\n")

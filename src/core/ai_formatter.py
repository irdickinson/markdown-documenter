from typing import Callable

import ollama

DEFAULT_MODEL = "doc-formatter"

# Instruction prefixes injected into the user message per formatting mode.
# "structured" uses the model's own system prompt unmodified.
_MODE_PREFIX: dict[str, str] = {
    "quick": (
        "FORMAT INSTRUCTION: Quick pass only. Add ## section headers at natural "
        "topic boundaries and fix obvious run-on sentences. Do not reorganise or "
        "reorder information. Prioritise speed over thoroughness.\n\n"
    ),
    "structured": "",
    "topic": (
        "FORMAT INSTRUCTION: Organise by theme. Identify all distinct topics and "
        "create a ## section for each one. Group related information together even "
        "if it was scattered in the original. Build a logical, readable flow.\n\n"
    ),
}


def doc_formatter_available() -> bool:
    try:
        models = ollama.list()
        return any(m.model.startswith(DEFAULT_MODEL) for m in models.models)
    except Exception:
        return False


def reformat_with_doc_formatter(
    content: str,
    formatting_mode: str = "structured",
    model: str = DEFAULT_MODEL,
    stop_flag: Callable[[], bool] | None = None,
) -> str:
    body = _strip_frontmatter(content)
    prefix = _MODE_PREFIX.get(formatting_mode, "")
    prompt = prefix + body

    stream = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    parts: list[str] = []
    for chunk in stream:
        if stop_flag and stop_flag():
            break
        token = chunk.message.content or ""
        parts.append(token)

    reformatted_body = "".join(parts).strip()
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

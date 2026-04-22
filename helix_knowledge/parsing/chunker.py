from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    text: str
    heading: str = ""
    index: int = 0


def chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 120, heading: str = "") -> list[TextChunk]:
    raw = (text or "").strip()
    if not raw:
        return []

    paragraphs = [part.strip() for part in raw.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [raw]

    chunks: list[TextChunk] = []
    current = ""
    index = 0

    def _push(value: str) -> None:
        nonlocal index
        clean = value.strip()
        if not clean:
            return
        chunks.append(TextChunk(text=clean, heading=heading, index=index))
        index += 1

    for para in paragraphs:
        candidate = para if not current else f"{current}\n\n{para}"
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            _push(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = (tail + "\n\n" + para).strip()
        else:
            start = 0
            while start < len(para):
                end = min(len(para), start + chunk_size)
                piece = para[start:end]
                _push(piece)
                start = max(end - overlap, end)
            current = ""

    if current:
        _push(current)

    return chunks

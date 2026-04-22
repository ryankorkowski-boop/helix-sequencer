from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re

_BLOCKED_TAGS = {"script", "style", "noscript", "svg", "nav", "aside"}
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_BREAK_TAGS = {"p", "div", "li", "tr", "br", "section", "article", "header", "footer"}
_BLOCKED_ATTR_TOKENS = {
    "sidebar",
    "navigation",
    "toc",
    "table-of-contents",
    "gitbook",
    "menu",
    "breadcrumb",
    "pager",
}
_NOISE_LINE_TOKENS = {
    "on this page",
    "powered by gitbook",
    "copy",
    "last updated",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._blocked_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attrs_text = " ".join((value or "").lower() for _key, value in attrs)
        has_blocked_attr = any(token in attrs_text for token in _BLOCKED_ATTR_TOKENS)
        if tag in _BLOCKED_TAGS or has_blocked_attr:
            self._blocked_depth += 1
            return
        if self._blocked_depth > 0:
            return
        if tag in _HEADING_TAGS:
            self.parts.append("\n## ")
        elif tag in _BLOCK_BREAK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _BLOCKED_TAGS and self._blocked_depth > 0:
            self._blocked_depth -= 1
            return
        if self._blocked_depth > 0:
            return
        if tag in _HEADING_TAGS or tag in _BLOCK_BREAK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._blocked_depth > 0:
            return
        text = unescape(data or "")
        if text.strip():
            self.parts.append(text)


def clean_html(html: str, *, max_chars: int = 24000) -> str:
    parser = _TextExtractor()
    parser.feed(html or "")
    merged = "".join(parser.parts)
    merged = re.sub(r"\r", "\n", merged)
    merged = re.sub(r"\n{3,}", "\n\n", merged)
    merged = re.sub(r"[ \t]{2,}", " ", merged)
    lines = [line.strip() for line in merged.splitlines()]
    filtered_lines: list[str] = []
    for line in lines:
        lower = line.lower()
        if not line:
            filtered_lines.append("")
            continue
        if any(token == lower or token in lower for token in _NOISE_LINE_TOKENS):
            continue
        filtered_lines.append(line)
    merged = "\n".join(filtered_lines).strip()
    if len(merged) > max_chars:
        merged = merged[:max_chars].rstrip() + " ..."
    return merged

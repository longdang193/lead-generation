from __future__ import annotations

from bs4 import BeautifulSoup


def soup_from_response(response: object) -> BeautifulSoup:
    content = getattr(response, "content", b"")
    if isinstance(content, (bytes, bytearray)) and content:
        return BeautifulSoup(content, "html.parser")
    return BeautifulSoup(str(getattr(response, "text", "") or ""), "html.parser")

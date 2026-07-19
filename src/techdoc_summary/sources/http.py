from __future__ import annotations

from urllib.error import URLError
from urllib.request import Request, urlopen


class DocumentFetchError(RuntimeError):
    pass


def fetch_text(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": "techdoc-summary/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as exc:
        raise DocumentFetchError(f"Failed to fetch {url}: {exc}") from exc

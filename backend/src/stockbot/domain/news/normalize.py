"""Text normalization for news items (① of the pipeline).

Two jobs:
  - ``clean_text`` : strip HTML tags + entities from titles/snippets (Naver/RSS
    wrap matched terms in <b> and HTML-escape quotes).
  - ``strip_boilerplate`` : remove KR news boilerplate that hurts hash accuracy —
    bracket tags ([속보]/[단독]/[종합]), the (서울=연합뉴스) dateline, and the
    reporter / 무단전재 tail. Used only to compute the exact-dedup hash, never to
    alter what we store.

Kept deliberately regex-only (no heavy NLP) per design — Phase 1 is cheap code.
"""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Leading bracket tags: [속보] [단독] [종합] [표] [사진] etc. (one or more).
_BRACKET_TAG_RE = re.compile(r"^(?:\s*\[[^\]]{1,12}\])+\s*")
# Dateline like "(서울=연합뉴스)" / "(세종=뉴스1)".
_DATELINE_RE = re.compile(r"\([^)]{1,12}=[^)]{1,20}\)")
# Reporter / copyright tail: "○○○ 기자", "무단전재 ...금지", "저작권자 ...".
_REPORTER_TAIL_RE = re.compile(r"[가-힣]{2,4}\s*기자.*$")
_COPYRIGHT_TAIL_RE = re.compile(r"(?:무단\s*전재|저작권자|ⓒ|©).*$")


def clean_text(value: str | None) -> str:
    """Strip HTML tags and unescape entities, then collapse whitespace.

    Tags are removed (not replaced with a space): Naver wraps the matched query
    term in inline <b> tags, so "<b>삼성</b>전자" must rejoin to "삼성전자" rather
    than split into "삼성 전자".
    """
    if not value:
        return ""
    text = _TAG_RE.sub("", value)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def strip_boilerplate(text: str) -> str:
    """Remove KR bracket tags / dateline / reporter-copyright tail (for hashing)."""
    if not text:
        return ""
    text = _BRACKET_TAG_RE.sub("", text)
    text = _DATELINE_RE.sub(" ", text)
    text = _COPYRIGHT_TAIL_RE.sub("", text)
    text = _REPORTER_TAIL_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()

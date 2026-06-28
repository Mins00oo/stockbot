"""News pipeline (Phase 1) tests — no real DB or network.

Covers exact-dedup helpers, ingestor normalization (fake clients), and the
run_ingest dedup orchestration (fake Toss + Finnhub + monkeypatched repository).
"""

from __future__ import annotations

import pytest

from stockbot.domain.news import service as news_service
from stockbot.domain.news import symbols as news_symbols
from stockbot.domain.news.dedup import canonical_url, exact_hash
from stockbot.domain.news.ingestors.finnhub_news import FinnhubNewsIngestor
from stockbot.domain.news.ingestors.naver_news import NaverNewsIngestor

# --------------------------------------------------------------------------- #
# ② Exact dedup — canonical_url
# --------------------------------------------------------------------------- #


def test_canonical_url_strips_tracking_and_fragment():
    u = "http://www.example.com/article?utm_source=x&id=5#top"
    assert canonical_url(u) == "https://www.example.com/article?id=5"


def test_canonical_url_naver_keeps_oid_aid_drops_sid():
    u = "https://n.news.naver.com/article?oid=001&aid=0000123&sid=101&rc=N"
    c = canonical_url(u)
    assert "oid=001" in c
    assert "aid=0000123" in c
    assert "sid=" not in c
    assert "rc=" not in c


def test_canonical_url_mobile_to_www_https_trailing_slash():
    assert canonical_url("http://m.example.com/a/") == "https://www.example.com/a"


def test_canonical_url_amp():
    assert canonical_url("https://www.example.com/a/amp") == "https://www.example.com/a"


# --------------------------------------------------------------------------- #
# ② Exact dedup — exact_hash
# --------------------------------------------------------------------------- #


def test_exact_hash_ignores_boilerplate_and_html_entities():
    # Bracket tag stripped; same underlying headline ⇒ same hash.
    assert exact_hash("[속보] 삼성전자 신고가") == exact_hash("삼성전자 신고가")


def test_exact_hash_differs_for_distinct_titles():
    assert exact_hash("A 관련 뉴스") != exact_hash("B 관련 뉴스")


# --------------------------------------------------------------------------- #
# Ingestor normalization
# --------------------------------------------------------------------------- #


class _FakeFinnhub:
    configured = True

    async def get_company_news(self, symbol, *, days=2):
        return [
            {
                "headline": "<b>Apple</b> beats estimates",
                "url": "https://example.com/a?utm_source=z",
                "summary": "good quarter",
                "datetime": 1_700_000_000,
                "id": 42,
                "related": "AAPL",
            }
        ]


class _FakeNaver:
    configured = True

    async def search_news(self, query, *, display=20, sort="date"):
        return [
            {
                "title": "<b>삼성</b>전자 신고가 &quot;호재&quot;",
                "originallink": "https://www.hankyung.com/article/1",
                "link": "https://n.news.naver.com/mirror",
                "description": "본문 요약 snippet",
                "pubDate": "Mon, 26 Sep 2022 10:00:00 +0900",
            }
        ]


@pytest.mark.asyncio
async def test_finnhub_ingestor_normalizes():
    items = await FinnhubNewsIngestor(_FakeFinnhub()).fetch("AAPL", "US", "Apple")
    assert len(items) == 1
    it = items[0]
    assert it.title == "Apple beats estimates"  # <b> stripped
    assert it.source == "finnhub"
    assert it.source_tickers == ["AAPL"]
    assert it.matched_by == "source_tag"
    assert it.published_at is not None
    assert it.raw_ref == "42"


@pytest.mark.asyncio
async def test_naver_ingestor_normalizes():
    items = await NaverNewsIngestor(_FakeNaver()).fetch("005930", "KR", "삼성전자")
    assert len(items) == 1
    it = items[0]
    assert "삼성전자 신고가" in it.title
    assert '"호재"' in it.title  # &quot; unescaped
    assert it.original_url == "https://www.hankyung.com/article/1"  # originallink, not mirror
    assert it.matched_by == "query"
    assert it.match_evidence == "삼성전자"
    assert it.published_at is not None


# --------------------------------------------------------------------------- #
# run_ingest orchestration + dedup
# --------------------------------------------------------------------------- #


class _FakeToss:
    def __init__(self, items):
        self._items = items

    async def get_holdings(self, account_seq):
        return {"items": self._items}


class _DupFinnhub:
    configured = True

    async def get_company_news(self, symbol, *, days=2):
        art = {
            "headline": "Apple news",
            "url": "https://example.com/a",
            "summary": "s",
            "datetime": 1_700_000_000,
            "id": 1,
            "related": symbol,
        }
        return [art, dict(art)]  # same article twice → one must be deduped


@pytest.mark.asyncio
async def test_run_ingest_dedups(monkeypatch):
    class _Creds:
        account_seq = "1"
        toss_app_key_enc = "x"
        toss_secret_key_enc = "y"

    async def fake_creds(session):
        return _Creds()

    monkeypatch.setattr(news_symbols.auth_repository, "get_credentials", fake_creds)

    store: set[str] = set()

    async def fake_exists(session, canonical, ehash):
        return canonical in store

    async def fake_insert(session, item, *, canonical_url, exact_hash, market):
        store.add(canonical_url)

    monkeypatch.setattr(news_service.repository, "exists", fake_exists)
    monkeypatch.setattr(news_service.repository, "insert_item", fake_insert)

    toss = _FakeToss([{"symbol": "AAPL", "marketCountry": "US", "name": "Apple"}])
    resp = await news_service.run_ingest(
        object(), toss_client=toss, finnhub_client=_DupFinnhub()
    )

    assert resp.symbols == 1
    assert resp.fetched == 2
    assert resp.stored == 1
    assert resp.deduped == 1
    assert resp.skipped is None


@pytest.mark.asyncio
async def test_run_ingest_skips_when_not_connected(monkeypatch):
    async def no_creds(session):
        return None

    monkeypatch.setattr(news_symbols.auth_repository, "get_credentials", no_creds)
    resp = await news_service.run_ingest(object())
    assert resp.skipped == "not_connected"
    assert resp.symbols == 0


@pytest.mark.asyncio
async def test_news_requires_pairing_key(client):
    resp = await client.get("/news")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

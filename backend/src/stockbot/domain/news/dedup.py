"""② Exact dedup — no ML, runs first, near-free (design §3).

Two keys catch most duplicates:
  - ``canonical_url`` : a stable URL identity (a DB unique index rejects re-fetches).
  - ``exact_hash``    : SHA-256 of the normalized title (+snippet), catching the
    same wire story re-published under different URLs.

URL normalization rules (design §3-A):
  - lowercase scheme/host, force https, drop default port / trailing slash / #fragment
  - strip tracking params (utm_*, fbclid, gclid, ref, spm, from, ...)
  - Naver: KEEP oid/aid (article identity), DROP sid/rc/cds
  - AMP/mobile: drop /amp + ?outputType=amp, m. → www.
We whitelist meaningful query params rather than blacklist, which is safer.
"""

from __future__ import annotations

import hashlib
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from stockbot.domain.news.normalize import strip_boilerplate

# Tracking params we always drop (design §3-A step 2).
_TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "ref",
    "spm",
    "from",
    "sid",  # Naver section id (not article identity)
    "rc",
    "cds",
    "igshid",
    "ocid",
}
# Query keys that identify the article and must be kept (e.g. Naver oid/aid).
_KEEP_PARAMS = {"oid", "aid", "id", "article_id", "articleid", "no"}


def _keep_param(key: str) -> bool:
    k = key.lower()
    if k in _KEEP_PARAMS:
        return True
    if k.startswith("utm_") or k in _TRACKING_PARAMS:
        return False
    # Default: keep unknown params (conservative — avoids merging distinct pages).
    return True


def canonical_url(raw_url: str | None) -> str:
    """Return a canonical form of ``raw_url`` for exact dedup. Best-effort: an
    unparseable URL is returned trimmed so it can still act as a unique key."""
    if not raw_url:
        return ""
    url = raw_url.strip()
    parts = urlsplit(url)
    if not parts.netloc:
        return url  # not an absolute URL — use as-is

    scheme = "https"
    host = parts.netloc.lower()
    # Drop default ports.
    if host.endswith(":80"):
        host = host[:-3]
    elif host.endswith(":443"):
        host = host[:-4]
    # Mobile → www.
    if host.startswith("m."):
        host = "www." + host[2:]

    path = parts.path
    # AMP normalization.
    if path.endswith("/amp"):
        path = path[: -len("/amp")]
    path = path.rstrip("/")

    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
            if _keep_param(k) and k.lower() != "outputtype"]
    kept.sort()
    query = urlencode(kept)

    # Drop fragment entirely.
    return urlunsplit((scheme, host, path, query, ""))


def exact_hash(title: str | None, snippet: str | None = None) -> str:
    """SHA-256 over the NFKC-normalized, boilerplate-stripped title (+snippet).

    Same normalized text ⇒ same hash ⇒ treated as the same article (catches wire
    re-syndication). O(1), language-agnostic.
    """
    base = (title or "").strip()
    if snippet:
        base = f"{base} {snippet.strip()}"
    base = unicodedata.normalize("NFKC", base)
    base = strip_boilerplate(base).lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

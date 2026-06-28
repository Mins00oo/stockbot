"""News pipeline domain.

Phase 1 scope (per docs/design/news-pipeline.md build plan P1):
  collect (ingestors) → normalize (RawItem) → exact dedup → store.

LLM triage/analysis, near-dup (SimHash), event clustering and filings are out of
scope here and land in later phases.
"""

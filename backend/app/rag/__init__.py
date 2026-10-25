"""RAG Engine Package for Mutual Fund FAQ Assistant.

Modules:
- entities: Entity extraction (scheme, field, aliases, disambiguation, pronoun resolution).
- facts: Direct O(1) SQLite fact path with deterministic contract templates.
- retriever: Metadata-prefiltered Hybrid Retriever (ChromaDB dense + BM25 lexical + RRF).
"""

from app.rag.entities import (
    FIELD_GLOSSARY,
    SCHEME_REGISTRY,
    EntityResolutionResult,
    get_disambiguation_response,
    get_scheme_meta,
    resolve_entities,
)
from app.rag.facts import (
    FACT_TEMPLATES,
    format_fact_response,
    get_fact_from_db,
    lookup_fact,
)
from app.rag.retriever import (
    HybridRetriever,
    RetrievalResult,
    RetrievedChunk,
    get_embedder,
    get_not_found_response,
)

__all__ = [
    "EntityResolutionResult",
    "SCHEME_REGISTRY",
    "FIELD_GLOSSARY",
    "resolve_entities",
    "get_disambiguation_response",
    "get_scheme_meta",
    "FACT_TEMPLATES",
    "get_fact_from_db",
    "format_fact_response",
    "lookup_fact",
    "RetrievedChunk",
    "RetrievalResult",
    "HybridRetriever",
    "get_embedder",
    "get_not_found_response",
]

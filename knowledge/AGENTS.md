# Knowledge Base Agent Guide

## Responsibilities & Stack
- **Scope**: Return policy chunking, dense/sparse embeddings, and hybrid retrieval using Qdrant.
- **Stack**: Qdrant Client, FastEmbed (`BAAI/bge-small-en-v1.5`, `Qdrant/bm25`), langchain-text-splitters.

## Key Directories & Entry Points
- `knowledge/knowledge_base.py`: `PolicyKnowledgeBase` hybrid ingestion and search.
- `knowledge/retriver.py`: Module search convenience entry point (`search_policy`).
- `knowledge/chunker.py`: Markdown section and clause parser.
- `knowledge/embeddings.py`: `EmbeddingService` for dense vector generation.
- `knowledge/policies/`: Markdown policy sources (`Policy.md`, `Policy-docs_V1.md`).

## Conventions & Rules
- Active Qdrant collection is `returnguard_policies` (do not use legacy name `policy_docs`).
- Hybrid search fuses dense and sparse BM25 scores via Reciprocal Rank Fusion (`Fusion.RRF`).
- Execute synchronous FastEmbed operations in threads to avoid blocking async event loops.
- Do not edit raw policy files unless explicitly instructed.

## Testing & Execution
- Search policy from CLI: `uv run python -m knowledge.retriver`.
- Inspect Qdrant dashboard: `http://localhost:6333/dashboard`.

## Docs to Read
- `docs/knowledge/RAG.md`.

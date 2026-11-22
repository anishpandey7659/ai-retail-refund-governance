# Policy Knowledge Base & RAG Specification

> Last verified against commit: `c39ba3f`

## Overview
Policy knowledge retrieval indexes return and refund policy documents into Qdrant for hybrid dense and sparse search.

- **Primary module**: `knowledge/knowledge_base.py` (`PolicyKnowledgeBase`).
- **Vector Database**: Qdrant 1.19 (`http://localhost:6333`).
- **Collection Name**: `returnguard_policies` (configured via `QDRANT_COLLECTION`; note: `infra/qdrant/collection.md` references legacy name `policy_docs`).

## Ingestion & Indexing Pipeline

```text
Policy Documents (knowledge/policies/*.md)
       |
       v
Markdown Chunking (knowledge/chunker.py)
  - Section-aware hierarchy (headers, paragraphs, bullet clauses)
  - Metadata: document_name, section, title, clause_id
       |
       +-------------------------------+
       |                               |
       v                               v
Dense Vector Embedding         Sparse Vector Embedding
(knowledge/embeddings.py)      (knowledge/knowledge_base.py)
FastEmbed: BAAI/bge-small-en-v1.5   FastEmbed: Qdrant/bm25
(or OpenAI text-embedding-3-small)  (sync execution in thread pool)
       |                               |
       +---------------+---------------+
                       |
                       v
            Qdrant Collection Upsert
         (named vectors: "dense", "sparse")
```

## Hybrid Search & Fusion (`knowledge_base.py:search_policy`)
1. **Query Encoding**:
   - Computes dense vector query via `EmbeddingService`.
   - Computes sparse BM25 token frequencies via `SparseTextEmbedding("Qdrant/bm25")`.
2. **Hybrid Search Execution**:
   - Queries Qdrant using `models.Prefetch` with both dense and sparse vector queries.
   - Merges candidate ranks using Reciprocal Rank Fusion (`models.FusionQuery(fusion=models.Fusion.RRF)`).
3. **Retrieval Output**:
   - Returns top-K policy chunks with score, section header, clause text, and policy source path.

## Source Policy Documents (`knowledge/policies/`)
- `Policy.md`: Active production return policy covering eligibility periods, exceptions, return condition requirements, and shipping rules.
- `Policy-docs_V1.md`: Version 1 reference documentation.

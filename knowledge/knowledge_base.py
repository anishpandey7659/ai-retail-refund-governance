import asyncio
import hashlib
import logging
import os
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from dotenv import load_dotenv
from fastembed import SparseTextEmbedding
from qdrant_client import AsyncQdrantClient, models

from .chunker import split_by_headings
from .embeddings import EmbeddingService


load_dotenv()

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"


class PolicyKnowledgeBase:
    """Ingest refund policy documents into Qdrant and search them with
    hybrid retrieval (dense embeddings + sparse BM25, fused with RRF)."""

    def __init__(self):
        self.qdrant = AsyncQdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333")
        )

        self.collection_name = os.getenv(
            "QDRANT_COLLECTION",
            "returnguard_policies",
        )

        self.embedding_service = EmbeddingService()

        # Sparse BM25 encoder (runs locally, downloads model on first use).
        self.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    # ------------------------------------------------------------------
    # Sparse embedding helpers (FastEmbed is sync, so run in a thread)
    # ------------------------------------------------------------------

    @staticmethod
    def _to_sparse_vector(embedding) -> models.SparseVector:
        return models.SparseVector(
            indices=embedding.indices.tolist(),
            values=embedding.values.tolist(),
        )

    async def _embed_sparse_documents(
        self, texts: list[str]
    ) -> list[models.SparseVector]:
        embeddings = await asyncio.to_thread(
            lambda: list(self.sparse_model.embed(texts))
        )
        return [self._to_sparse_vector(e) for e in embeddings]

    async def _embed_sparse_query(self, query: str) -> models.SparseVector:
        embedding = await asyncio.to_thread(
            lambda: next(iter(self.sparse_model.query_embed(query)))
        )
        return self._to_sparse_vector(embedding)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def create_collection(
        self,
        vector_size: int = 1536,
        recreate: bool = False,
    ):
        """Create a collection with a named dense vector and a sparse BM25 vector."""

        if recreate and await self.qdrant.collection_exists(
            self.collection_name
        ):
            await self.qdrant.delete_collection(self.collection_name)
            logger.info("Deleted Qdrant collection: %s", self.collection_name)

        exists = await self.qdrant.collection_exists(self.collection_name)

        if not exists:
            await self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    DENSE_VECTOR_NAME: models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                },
                sparse_vectors_config={
                    SPARSE_VECTOR_NAME: models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    ),
                },
            )

            logger.info(
                "Created Qdrant collection: %s",
                self.collection_name,
            )
            return

        # Collection already exists: make sure it has the expected schema.
        info = await self.qdrant.get_collection(self.collection_name)
        vectors = info.config.params.vectors
        sparse = info.config.params.sparse_vectors or {}

        if (
            not isinstance(vectors, dict)
            or DENSE_VECTOR_NAME not in vectors
            or SPARSE_VECTOR_NAME not in sparse
        ):
            raise RuntimeError(
                f"Collection '{self.collection_name}' exists with an old "
                "schema (no named dense + sparse vectors). Re-run ingestion "
                "with recreate_collection=True to rebuild it."
            )

        logger.info(
            "Collection '%s' already exists with hybrid schema.",
            self.collection_name,
        )

    @staticmethod
    def generate_point_id(
        document_id: str,
        policy_version: str,
        chunk_text: str,
    ) -> str:
        """Generate a deterministic UUID for each policy chunk.

        policy_version is part of the ID so different versions of the same
        document can coexist instead of overwriting each other.
        """

        content_hash = hashlib.sha256(
            chunk_text.encode("utf-8")
        ).hexdigest()

        return str(
            uuid5(
                NAMESPACE_URL,
                f"{document_id}:{policy_version}:{content_hash}",
            )
        )

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    async def ingest_policy(
        self,
        file_path: str,
        document_id: str,
        policy_version: str,
        effective_date: str,
        status: str = "active",
        recreate_collection: bool = False,
    ):
        """Split, embed (dense + sparse), and store a policy document."""

        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Policy document not found: {file_path}"
            )

        logger.info("Starting policy ingestion: %s", path.name)

        # 1. Split policy into LangChain Documents.
        documents = split_by_headings(str(path))

        if not documents:
            raise ValueError("No policy sections were generated.")

        # 2. Generate dense embeddings.
        vectors = await self.embedding_service.embed_documents(documents)

        if len(documents) != len(vectors):
            raise ValueError("Document and embedding counts do not match.")

        vector_size = len(vectors[0])

        if any(len(vector) != vector_size for vector in vectors):
            raise ValueError("Inconsistent embedding dimensions.")

        # 3. Generate sparse BM25 embeddings.
        sparse_vectors = await self._embed_sparse_documents(
            [document.page_content for document in documents]
        )

        if len(sparse_vectors) != len(documents):
            raise ValueError(
                "Document and sparse embedding counts do not match."
            )

        # 4. Create collection if necessary.
        await self.create_collection(
            vector_size=vector_size,
            recreate=recreate_collection,
        )

        # 5. Build Qdrant points.
        points = []

        for index, (document, vector, sparse_vector) in enumerate(
            zip(documents, vectors, sparse_vectors)
        ):
            chunk_id = self.generate_point_id(
                document_id,
                policy_version,
                document.page_content,
            )

            payload = {
                **document.metadata,
                "document_id": document_id,
                "policy_version": policy_version,
                "effective_date": effective_date,
                "status": status,
                "source": path.name,
                "chunk_index": index,
                "content": document.page_content,
            }

            points.append(
                models.PointStruct(
                    id=chunk_id,
                    vector={
                        DENSE_VECTOR_NAME: vector,
                        SPARSE_VECTOR_NAME: sparse_vector,
                    },
                    payload=payload,
                )
            )

        # 6. Upsert into Qdrant.
        await self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        logger.info(
            "Successfully ingested %d policy chunks.",
            len(points),
        )

        return {
            "document_id": document_id,
            "policy_version": policy_version,
            "total_chunks": len(points),
            "vector_dimensions": vector_size,
            "collection": self.collection_name,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_policy(self, query: str, limit: int = 5):
        """Retrieve policy chunks using hybrid dense + sparse BM25 search."""

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not 1 <= limit <= 20:
            raise ValueError("Limit must be between 1 and 20.")

        query = query.strip()

        # 1. Generate dense and sparse query embeddings.
        query_vector = await self.embedding_service.embed_text(text=query)
        sparse_query = await self._embed_sparse_query(query)

        # 2. Hybrid retrieval, fused with Reciprocal Rank Fusion.
        results = await self.qdrant.query_points(
            collection_name=self.collection_name,
            prefetch=[
                # Dense semantic search
                models.Prefetch(
                    query=query_vector,
                    using=DENSE_VECTOR_NAME,
                    limit=20,
                ),
                # Sparse BM25 keyword search
                models.Prefetch(
                    query=sparse_query,
                    using=SPARSE_VECTOR_NAME,
                    limit=20,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )

        # 3. Format results.
        return [
            {
                "score": point.score,
                "content": (point.payload or {}).get("content"),
                "document_id": (point.payload or {}).get("document_id"),
                "policy_version": (point.payload or {}).get("policy_version"),
                "section": (point.payload or {}).get("section"),
                "effective_date": (point.payload or {}).get("effective_date"),
            }
            for point in results.points
        ]


async def main():
    logging.basicConfig(level=logging.INFO)

    knowledge_base = PolicyKnowledgeBase()

    try:
        result = await knowledge_base.ingest_policy(
            file_path="knowledge/policies/Policy-docs_V1.md",
            document_id="RG-POL-001",
            policy_version="1.0",
            effective_date="2026-10-30",
            # Set to True once to rebuild the old collection with the new schema.
            recreate_collection=True,
        )

        print("\nIngestion Result:")
        print(result)

    finally:
        await knowledge_base.qdrant.close()
        await knowledge_base.embedding_service.client.close()


if __name__ == "__main__":
    asyncio.run(main())


# uv run python -m knowledge.ingestion
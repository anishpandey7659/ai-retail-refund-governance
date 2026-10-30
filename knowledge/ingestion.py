
import hashlib
import logging
import os
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

from .chunker import split_by_headings
from .embeddings import EmbeddingService


load_dotenv()

logger = logging.getLogger(__name__)


class PolicyIngestion:
    """Ingest refund policy documents into Qdrant."""

    def __init__(self):
        self.qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333")
        )

        self.collection_name = os.getenv(
            "QDRANT_COLLECTION",
            "returnguard_policies",
        )

        self.embedding_service = EmbeddingService()

    def create_collection(self, vector_size: int = 1536):
        """Create the Qdrant collection if it does not exist."""

        if self.qdrant.collection_exists(self.collection_name):
            logger.info(
                "Collection '%s' already exists.",
                self.collection_name,
            )
            return

        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        logger.info(
            "Created Qdrant collection: %s",
            self.collection_name,
        )

    @staticmethod
    def generate_point_id(document_id: str, chunk_text: str) -> str:
        """Generate a deterministic UUID for each policy chunk."""

        content_hash = hashlib.sha256(
            chunk_text.encode("utf-8")
        ).hexdigest()

        return str(
            uuid5(
                NAMESPACE_URL,
                f"{document_id}:{content_hash}",
            )
        )

    def ingest_policy(
        self,
        file_path: str,
        document_id: str,
        policy_version: str,
        effective_date: str,
        status: str = "active",
    ):
        """Split, embed, and store a policy document."""

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

        # 2. Generate embeddings.
        vectors = self.embedding_service.embed_documents(documents)

        if len(documents) != len(vectors):
            raise ValueError("Document and embedding counts do not match.")

        vector_size = len(vectors[0])

        if any(len(vector) != vector_size for vector in vectors):
            raise ValueError("Inconsistent embedding dimensions.")

        # 3. Create collection if necessary.
        self.create_collection(vector_size=vector_size)

        # 4. Build Qdrant points.
        points = []

        for index, (document, vector) in enumerate(
            zip(documents, vectors)
        ):
            chunk_id = self.generate_point_id(
                document_id,
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
                    vector=vector,
                    payload=payload,
                )
            )

        # 5. Upsert into Qdrant.
        self.qdrant.upsert(
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    ingestion = PolicyIngestion()

    result = ingestion.ingest_policy(
        file_path=(
            "knowledge/policies/Policy-docs_V1.md"
        ),
        document_id="RG-POL-001",
        policy_version="1.0",
        effective_date="2026-10-30",
    )

    print("\nIngestion Result:")
    print(result)

# uv run python knowledge/ingestion.py
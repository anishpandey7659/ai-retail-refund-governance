import os

from openai import OpenAI
from langchain_core.documents import Document


class EmbeddingService:
    """Generate embeddings using OpenAI."""

    def __init__(self):
        self.client = OpenAI()

        self.model = os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        )

        self.batch_size = 100

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    def embed_documents(
        self,
        documents: list[Document],
    ) -> list[list[float]]:
        """Generate embeddings for multiple LangChain documents."""

        if not documents:
            return []

        texts = [doc.page_content for doc in documents]

        embeddings = []

        # Process documents in batches.
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]

            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
            )

            # Preserve the original document ordering.
            batch_embeddings = sorted(
                response.data,
                key=lambda item: item.index,
            )

            embeddings.extend(
                item.embedding for item in batch_embeddings
            )

        return embeddings


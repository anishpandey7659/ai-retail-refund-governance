
import re
from pathlib import Path

from langchain_core.documents import Document


def split_by_headings(file_path: str) -> list[Document]:
    """
    Split a Markdown policy document by ## and ### headings.

    Each section becomes a LangChain Document with metadata
    containing its heading hierarchy.
    """

    text = Path(file_path).read_text(encoding="utf-8")

    # Match only level 2 and level 3 headings.
    heading_pattern = re.compile(
        r"^(#{2,3})\s+(.+?)\s*$",
        re.MULTILINE,
    )

    matches = list(heading_pattern.finditer(text))

    documents: list[Document] = []

    current_h2: str | None = None

    for index, match in enumerate(matches):
        heading_level = len(match.group(1))
        heading_title = match.group(2).strip()

        start = match.start()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        content = text[start:end].strip()

        if heading_level == 2:
            current_h2 = heading_title
            current_h3 = None

        else:
            current_h3 = heading_title

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "heading_level": heading_level,
                    "parent_section": current_h2,
                    "section": heading_title,
                },
            )
        )

    return documents


if __name__ == "__main__":
    chunks = split_by_headings(
        "knowledge/policies/Policy-docs_V1.md"
    )

    print(f"Total chunks: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {index} ---")
        print("Metadata:", chunk.metadata)
        print("Content:", chunk.page_content)

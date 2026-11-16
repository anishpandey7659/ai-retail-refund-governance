import re
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

REASON_CODES = ["damaged", "defective", "wrong_item", "not_as_described",
                "quality", "arrived_late", "no_longer_needed"]

# not policy rules -> never retrieve these
SKIP_SECTIONS = ("Document control", "Out of scope", "Test scenarios", "Change log")


def split_policy(file_path: str, chunk_size: int = 1200) -> list:
    with open(file_path, encoding="utf-8") as f:
        text = f.read()

    md = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "doc"), ("##", "section"), ("###", "subsection")],
        strip_headers=False,
    )
    rec = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=0)
    docs = rec.split_documents(md.split_text(text))

    out = []
    table_headers = {}  # (section, subsection) -> first two table lines

    for d in docs:
        section = d.metadata.get("section")
        subsection = d.metadata.get("subsection")

        # drop intro and non-policy sections
        if not section or any(s in section for s in SKIP_SECTIONS):
            continue

        content = d.page_content.replace("  \n", "\n").strip()
        lines = content.splitlines()
        key = (section, subsection)

        # remember the table header the first time we see a table in this section
        for i in range(len(lines) - 1):
            if lines[i].startswith("|") and lines[i + 1].startswith("| ---"):
                table_headers.setdefault(key, f"{lines[i]}\n{lines[i + 1]}")
                break

        # continuation table chunk (starts with a row, not a header) -> add header row
        is_cut_table = (content.startswith("|")
                        and not (len(lines) > 1 and lines[1].startswith("| ---")))
        if is_cut_table and key in table_headers:
            content = f"{table_headers[key]}\n{content}"

        # continuation chunk (no heading) -> add heading
        if not content.startswith("#"):
            heading = f"### {subsection}" if subsection else f"## {section}"
            content = f"{heading}\n\n{content}"

        num = re.match(r"(\d+)\.", section)
        out.append(type(d)(
            page_content=content,
            metadata={
                "section": section,
                "section_no": int(num.group(1)) if num else 0,
                "subsection": subsection or "",
                "reason_codes": [r for r in REASON_CODES if f"`{r}`" in content],
                "has_table": "| ---" in content,
            },
        ))
    return out

if __name__ == "__main__":
    chunks=split_policy(file_path="/home/anish/Documents/Project/Retail-Refund/knowledge/policies/Policy.md")
    print(len(chunks))
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    document_name: str
    section_title: str
    chunk_text: str


def knowledge_base_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "knowledge_base"


def _read_markdown_files() -> list[tuple[str, str]]:
    base_dir = knowledge_base_dir()
    if not base_dir.exists():
        return []

    return [(path.stem, path.read_text(encoding="utf-8")) for path in sorted(base_dir.glob("*.md"))]


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", markdown, flags=re.MULTILINE))
    if not matches:
        return [("Overview", markdown.strip())]

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        title = match.group(2).strip()
        body = markdown[start:end].strip()
        if body:
            sections.append((title, body))
    return sections


def _chunk_text(text: str, max_words: int = 640, overlap: int = 80) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]).strip())
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def load_knowledge_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for document_name, markdown in _read_markdown_files():
        for section_index, (section_title, section_body) in enumerate(_split_sections(markdown)):
            for chunk_index, chunk_text in enumerate(_chunk_text(section_body)):
                chunks.append(
                    KnowledgeChunk(
                        # A document can have several sections whose first
                        # chunk would otherwise all be `<document>:0`.
                        id=f"{document_name}:{section_index}:{chunk_index}",
                        document_name=document_name,
                        section_title=section_title,
                        chunk_text=chunk_text,
                    )
                )
    return chunks

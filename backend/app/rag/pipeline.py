"""Document parsing, LangChain chunking and Gemini vectorization."""
from __future__ import annotations

import hashlib
import io
import math
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Any

from fastapi import HTTPException

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 180_000
MAX_PAGES = 40
MAX_CHUNKS = 200
CHUNK_SIZE = 900
CHUNK_OVERLAP = 140
EMBEDDING_DIMENSIONS = 768
EMBEDDING_MODEL = "gemini-embedding-001"
CONTENT_TYPES = {".pdf": "application/pdf", ".md": "text/markdown", ".txt": "text/plain"}

@dataclass(frozen=True)
class PolicyChunk:
    content: str
    page_number: int | None
    index: int

def sanitized_filename(filename: str | None) -> tuple[str, str]:
    name = PurePosixPath((filename or "").replace(chr(92), "/")).name
    name = re.sub(r"[\\x00-\\x1f\\x7f]", "", name).strip()
    if not name or len(name) > 180 or name.startswith("."):
        raise HTTPException(status_code=422, detail="Invalid document filename")
    extension = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension not in CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only .pdf, .txt and .md policies are supported")
    return name, CONTENT_TYPES[extension]

def extract_pages(data: bytes, mime: str) -> list[tuple[int | None, str]]:
    if not data:
        raise HTTPException(status_code=422, detail="Document is empty")
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Document exceeds 2 MB")
    if mime == "application/pdf":
        if not data.startswith(b"%PDF-"):
            raise HTTPException(status_code=422, detail="Uploaded file is not a valid PDF")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data), strict=True)
            if reader.is_encrypted or len(reader.pages) > MAX_PAGES:
                raise ValueError("Encrypted or oversized PDF")
            pages = []
            total = 0
            for page_no, page in enumerate(reader.pages, 1):
                text = (page.extract_text() or "").replace(chr(0), " ").strip()
                total += len(text)
                if total > MAX_TEXT_CHARS:
                    raise HTTPException(status_code=413, detail="Extracted content is too large")
                if text:
                    pages.append((page_no, text))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Could not read PDF. Upload a text-based, unencrypted PDF") from exc
    else:
        try:
            text = data.decode("utf-8-sig").replace(chr(0), " ").strip()
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=422, detail="Text files must use UTF-8") from exc
        if len(text) > MAX_TEXT_CHARS:
            raise HTTPException(status_code=413, detail="Extracted content is too large")
        pages = [(None, text)] if text else []
    if not pages:
        raise HTTPException(status_code=422, detail="No readable text found; scanned PDFs require OCR")
    return pages

def split_pages(pages: list[tuple[int | None, str]]) -> list[PolicyChunk]:
    """LangChain splitting preserves original PDF page numbers for citations."""
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    documents = [Document(page_content=content, metadata={"page_number": page}) for page, content in pages]
    pieces = splitter.split_documents(documents)
    if not pieces or len(pieces) > MAX_CHUNKS:
        raise HTTPException(status_code=413, detail="Document produces too many chunks (maximum 200)")
    return [PolicyChunk(content=d.page_content.strip(), page_number=d.metadata["page_number"], index=i)
            for i, d in enumerate(pieces) if d.page_content.strip()]

@lru_cache(maxsize=1)
def embeddings_client():
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=503, detail="Set GOOGLE_API_KEY on the backend to use policy RAG")
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model=f"models/{EMBEDDING_MODEL}", output_dimensionality=EMBEDDING_DIMENSIONS)

def checked_vector(vector: Any) -> list[float]:
    if not isinstance(vector, (list, tuple)) or len(vector) != EMBEDDING_DIMENSIONS:
        raise HTTPException(status_code=502, detail="Embedding provider returned wrong dimensions")
    try:
        floats = [float(x) for x in vector]
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Embedding provider returned invalid numbers") from exc
    if not all(math.isfinite(v) for v in floats) or not any(floats):
        raise HTTPException(status_code=502, detail="Embedding provider returned invalid vector")
    return floats

async def embed_chunks(chunks: list[PolicyChunk]) -> list[list[float]]:
    model = embeddings_client()
    result: list[list[float]] = []
    for start in range(0, len(chunks), 16):
        batch = chunks[start:start + 16]
        vectors = await model.aembed_documents([c.content for c in batch])
        if len(vectors) != len(batch):
            raise HTTPException(status_code=502, detail="Embedding provider returned wrong batch size")
        result.extend(checked_vector(vector) for vector in vectors)
    return result

async def embed_question(question: str) -> list[float]:
    return checked_vector(await embeddings_client().aembed_query(question))

def content_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

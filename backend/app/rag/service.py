"""User-scoped policy persistence, cleanup, and semantic retrieval."""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID
from fastapi import HTTPException
from app.core.supabase import CurrentUser
from app.rag.pipeline import (
    EMBEDDING_MODEL, content_sha256, embed_chunks, embed_question,
    extract_pages, sanitized_filename, split_pages,
)
from app.services.postgrest import owner_filter, query, rpc

logger = logging.getLogger(__name__)

def first(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise HTTPException(status_code=404, detail="Policy document not found")
    return rows[0]

async def ingest(user: CurrentUser, *, filename: str, title: str, data: bytes) -> dict[str, Any]:
    """Mark ready only after all chunks were embedded and persisted."""
    filename, mime = sanitized_filename(filename)
    pages = extract_pages(data, mime)
    chunks = split_pages(pages)
    digest = content_sha256(data)
    existing = await query(user, "knowledge_documents", params=owner_filter(user,
        content_sha256=f"eq.{digest}", select="id,status", limit=1))
    if existing:
        if existing[0]["status"] != "failed":
            raise HTTPException(status_code=409, detail="This document is already uploaded or processing")
        await query(user, "knowledge_documents", method="DELETE",
            params=owner_filter(user, id=f"eq.{existing[0]['id']}"))
    created = await query(user, "knowledge_documents", method="POST", data={
        "owner_id": user.id, "filename": filename, "title": title,
        "content_type": mime, "content_sha256": digest, "embedding_model": EMBEDDING_MODEL,
        "status": "processing",
    })
    record = first(created)
    doc_id = record["id"]
    try:
        embeddings = await embed_chunks(chunks)
        rows = [{
            "owner_id": user.id, "document_id": doc_id, "chunk_index": chunk.index,
            "page_number": chunk.page_number, "content": chunk.content, "embedding": vector,
        } for chunk, vector in zip(chunks, embeddings, strict=True)]
        for offset in range(0, len(rows), 20):
            await query(user, "knowledge_chunks", method="POST", data=rows[offset:offset+20])
        return first(await query(user, "knowledge_documents", method="PATCH",
            params=owner_filter(user, id=f"eq.{doc_id}"),
            data={"status": "ready", "chunk_count": len(chunks), "error_message": None}))
    except Exception:
        logger.exception("Policy ingestion failed (document id=%s)", doc_id)
        try:
            await query(user, "knowledge_chunks", method="DELETE",
                params=owner_filter(user, document_id=f"eq.{doc_id}"))
            await query(user, "knowledge_documents", method="PATCH",
                params=owner_filter(user, id=f"eq.{doc_id}"),
                data={"status": "failed", "chunk_count": 0, "error_message": "Ingestion failed; re-upload to retry"})
        except Exception:
            logger.exception("Unable to mark failed ingestion (document id=%s)", doc_id)
        raise

async def list_documents(user: CurrentUser) -> list[dict[str, Any]]:
    return await query(user, "knowledge_documents", params=owner_filter(user,
        select="id,title,filename,content_type,status,chunk_count,created_at,updated_at,error_message",
        order="created_at.desc", limit=100))

async def delete_document(user: CurrentUser, document_id: UUID) -> None:
    rows = await query(user, "knowledge_documents", method="DELETE",
        params=owner_filter(user, id=f"eq.{document_id}"))
    first(rows)

async def retrieve(user: CurrentUser, question: str, threshold: float, top_k: int) -> list[dict[str, Any]]:
    vector = await embed_question(question)
    return await rpc(user, "match_policy_chunks", {
        "query_embedding": vector, "match_threshold": threshold, "match_count": top_k,
    })

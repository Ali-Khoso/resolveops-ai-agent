"""Authenticated policy upload, list, delete and question-answer endpoints."""
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from app.core.supabase import CurrentUser, get_current_user
from app.rag.answer import PolicyAnswer, PolicyQuestion, answer_policy
from app.rag.pipeline import MAX_FILE_BYTES, sanitized_filename
from app.rag.service import delete_document, ingest, list_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workspace/knowledge", tags=["Knowledge Base (authenticated)"])

@router.get("/documents")
async def documents(user: CurrentUser = Depends(get_current_user)):
    return {"items": await list_documents(user)}

@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(..., min_length=1, max_length=160),
    user: CurrentUser = Depends(get_current_user),
):
    if not title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be blank")
    sanitized_filename(file.filename)  # Reject unsupported files before reading them.
    try:
        data = await file.read(MAX_FILE_BYTES + 1)
    finally:
        await file.close()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Policy file exceeds 2 MB")
    try:
        return await ingest(user, filename=file.filename or "", title=title.strip(), data=data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Knowledge upload failed")
        raise HTTPException(status_code=502, detail="Knowledge ingestion failed; check backend logs") from exc

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(document_id: UUID, user: CurrentUser = Depends(get_current_user)):
    await delete_document(user, document_id)
    return Response(status_code=204)

@router.post("/ask", response_model=PolicyAnswer)
async def ask(question: PolicyQuestion, user: CurrentUser = Depends(get_current_user)):
    try:
        return await answer_policy(user, question)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Knowledge Q&A failed")
        raise HTTPException(status_code=502, detail="Knowledge question failed; check Gemini configuration") from exc

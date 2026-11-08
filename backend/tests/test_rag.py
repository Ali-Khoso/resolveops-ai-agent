"""Offline Phase 3 RAG tests: no real Supabase or Google calls."""
from uuid import UUID
import asyncio
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.supabase import CurrentUser, get_current_user, get_config
from app.rag import pipeline, service, answer
from app.services.postgrest import rpc

USER="11111111-1111-4111-8111-111111111111"
DOC="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

@pytest.fixture
def client():
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()

def authenticated():
    app.dependency_overrides[get_current_user]=lambda:CurrentUser(USER,"a@example.com","verified.jwt")

def test_anonymous_knowledge_requires_auth(client):
    assert client.get("/api/v1/workspace/knowledge/documents").status_code==401
    assert client.post("/api/v1/workspace/knowledge/ask",json={"question":"Refund time?"}).status_code==401
    assert client.delete(f"/api/v1/workspace/knowledge/documents/{DOC}").status_code==401

def test_extension_validation_and_windows_paths():
    assert pipeline.sanitized_filename("C:\\fakepath\\returns.txt")==("returns.txt","text/plain")
    with pytest.raises(HTTPException) as exc: pipeline.sanitized_filename("bad.exe")
    assert exc.value.status_code==415

def test_text_parser_and_bad_pdf():
    assert pipeline.extract_pages(b"Refund within 30 days","text/plain")==[(None,"Refund within 30 days")]
    with pytest.raises(HTTPException):pipeline.extract_pages(b"notpdf","application/pdf")
    with pytest.raises(HTTPException):pipeline.extract_pages(b"\xff","text/plain")

def test_size_limit_and_bad_vectors():
    with pytest.raises(HTTPException):pipeline.extract_pages(b"x"*(pipeline.MAX_FILE_BYTES+1),"text/plain")
    for vector in [[0]*768,[float("nan")]*768,[1]*10]:
        with pytest.raises(HTTPException):pipeline.checked_vector(vector)
    assert len(pipeline.checked_vector([0.1]*768))==768

def test_authenticated_document_list(client,monkeypatch):
    import app.api.knowledge as route
    authenticated()
    async def fake(user):assert user.id==USER;return [{"id":DOC,"title":"Returns"}]
    monkeypatch.setattr(route,"list_documents",fake)
    assert client.get("/api/v1/workspace/knowledge/documents").json()["items"][0]["id"]==DOC

def test_upload_invalid_title_and_extension(client):
    authenticated()
    assert client.post("/api/v1/workspace/knowledge/documents",data={"title":"Returns"},files={"file":("bad.exe",b"text")}).status_code==415
    assert client.post("/api/v1/workspace/knowledge/documents",data={"title":"  "},files={"file":("good.txt",b"text")}).status_code==422

def test_ingestion_marks_ready_only_after_embeddings(monkeypatch):
    user=CurrentUser(USER,None,"jwt")
    events=[]
    async def fake_query(actor,table,**opts):
        assert actor.id==USER
        events.append((table,opts))
        if table=="knowledge_documents" and opts.get("method","GET")=="GET":return []
        if table=="knowledge_documents" and opts.get("method")=="POST":return [{"id":DOC}]
        if table=="knowledge_documents" and opts.get("method")=="PATCH":return [{"id":DOC,**opts["data"]}]
        return []
    async def vectors(chunks):return [[0.2]*768]
    monkeypatch.setattr(service,"query",fake_query)
    monkeypatch.setattr(service,"split_pages",lambda pages:[pipeline.PolicyChunk("30-day refund",None,0)])
    monkeypatch.setattr(service,"embed_chunks",vectors)
    result=asyncio.run(service.ingest(user,filename="policy.txt",title="Policy",data=b"30-day refund"))
    assert result["status"]=="ready" and result["chunk_count"]==1
    assert any(table=="knowledge_chunks" and opts["data"][0]["owner_id"]==USER for table,opts in events)
    assert events[-1][1]["data"]["status"]=="ready"

def test_failed_embedding_marks_doc_failed(monkeypatch):
    user=CurrentUser(USER,None,"jwt")
    seen=[]
    async def fake_query(actor,table,**opts):
        if table=="knowledge_documents" and opts.get("method","GET")=="GET":return []
        if table=="knowledge_documents" and opts.get("method")=="POST":return [{"id":DOC}]
        if table=="knowledge_documents" and opts.get("method")=="PATCH":seen.append(opts["data"]["status"]);return [{"id":DOC}]
        return []
    async def fail(_):raise RuntimeError("Mock failure")
    monkeypatch.setattr(service,"query",fake_query)
    monkeypatch.setattr(service,"split_pages",lambda pages:[pipeline.PolicyChunk("Policy",None,0)])
    monkeypatch.setattr(service,"embed_chunks",fail)
    with pytest.raises(RuntimeError):asyncio.run(service.ingest(user,filename="p.txt",title="P",data=b"Policy"))
    assert seen==["failed"]

@pytest.mark.asyncio
async def test_rpc_forwards_end_user_jwt(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL","https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY","publishable")
    get_config.cache_clear()
    def handler(request):
        assert request.url.path=="/rest/v1/rpc/match_policy_chunks"
        assert request.headers["authorization"]=="Bearer verified.jwt"
        assert request.headers["apikey"]=="publishable"
        return httpx.Response(200,json=[])
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,"AsyncClient",lambda *a,**k:original(transport=httpx.MockTransport(handler),**k))
    assert await rpc(CurrentUser(USER,None,"verified.jwt"),"match_policy_chunks",{"query_embedding":[.1]*768})==[]
    get_config.cache_clear()

@pytest.mark.asyncio
async def test_no_matches_abstains_without_llm(monkeypatch):
    async def empty(*a,**k):return []
    async def fail(*a,**k):raise AssertionError("Gemini should not be called")
    monkeypatch.setattr(answer,"retrieve",empty)
    monkeypatch.setattr(answer,"generate_answer",fail)
    response=await answer.answer_policy(CurrentUser(USER,None,"jwt"),answer.PolicyQuestion(question="Refund period?"))
    assert not response.grounded and not response.sources

@pytest.mark.asyncio
async def test_citation_validation(monkeypatch):
    row={"document_id":DOC,"title":"Refunds","filename":"returns.txt","page_number":1,"chunk_index":0,"similarity":.88,"content":"Refund within 30 days"}
    async def hits(*a,**k):return [row]
    async def good(*a,**k):return "Refunds are allowed within 30 days [1]."
    async def bad(*a,**k):return "Sure, the refund is complete [7]."
    monkeypatch.setattr(answer,"retrieve",hits)
    monkeypatch.setattr(answer,"generate_answer",good)
    user=CurrentUser(USER,None,"jwt")
    ok=await answer.answer_policy(user,answer.PolicyQuestion(question="How long?"))
    assert ok.grounded and ok.sources[0].page_number==1
    monkeypatch.setattr(answer,"generate_answer",bad)
    denied=await answer.answer_policy(user,answer.PolicyQuestion(question="How long?"))
    assert not denied.grounded

def test_unknown_fields_are_rejected(client):
    authenticated()
    assert client.post("/api/v1/workspace/knowledge/ask",json={"question":"Refund period?","owner_id":USER}).status_code==422
    assert client.post("/api/v1/workspace/knowledge/ask",json={"question":"Refund period?","top_k":20}).status_code==422

def test_sql_enforces_auth_and_invoker():
    from pathlib import Path
    sql=(Path(__file__).parents[2]/"supabase/migrations/202611090001_phase3_knowledge_rag.sql").read_text()
    assert "security invoker" in sql.lower() and "auth.uid()" in sql
    assert "enable row level security" in sql.lower()

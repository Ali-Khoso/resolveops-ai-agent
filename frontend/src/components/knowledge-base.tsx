"use client";
import {useCallback, useEffect, useRef, useState, type FormEvent} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {ArrowLeft, BookOpen, CheckCircle2, FileText, Loader2, Send, ShieldCheck, Sparkles, Trash2, UploadCloud} from "lucide-react";
import {getSupabase} from "@/lib/supabase";
import {askPolicies, listPolicyDocuments, removePolicyDocument, uploadPolicy, type PolicyAnswer, type PolicyDocument} from "@/lib/knowledge-api";

const examples = ["How long can I request a refund?", "What if my delivery arrived damaged?", "How do I track an order?"];
export default function KnowledgeBase() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<PolicyDocument[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState("");
  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<PolicyAnswer | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const refresh = useCallback(async () => {
    const response = await listPolicyDocuments();
    setDocuments(response.items);
  }, []);
  useEffect(() => {
    let active = true;
    async function initialize() {
      const supabase = getSupabase();
      if (!supabase) {
        if (active) {setError("Supabase isn't configured. Add your project URL and publishable key."); setLoading(false);}
        return;
      }
      const {data, error: authError} = await supabase.auth.getUser();
      if (!data.user || authError) {router.replace("/login"); return;}
      try {await refresh();}
      catch (err) {if (active) setError(err instanceof Error ? err.message : "Could not load policies");}
      finally {if (active) setLoading(false);}
    }
    void initialize();
    return () => {active = false;};
  }, [refresh, router]);
  function chooseFile(next: File | null) {
    setFile(next); setError("");
    if (next) setTitle(next.name.replace(/\.(txt|md|pdf)$/i,"").replace(/[-_]/g," ").slice(0,160));
  }
  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setNotice("");
    if (!file || !title.trim()) {setError("Choose a file and policy title."); return;}
    if (file.size > 2 * 1024 * 1024) {setError("Document size must be at most 2 MB."); return;}
    setUploading(true);
    try {
      await uploadPolicy(file, title.trim());
      setFile(null); setTitle("");
      if (fileRef.current) fileRef.current.value="";
      await refresh(); setNotice("The policy has been indexed and is ready to search.");
    } catch (err) {setError(err instanceof Error ? err.message : "Indexing failed");}
    finally {setUploading(false);}
  }
  async function onDelete(doc: PolicyDocument) {
    if (!window.confirm(`Delete "${doc.title}" and all its indexed chunks?`)) return;
    setDeleting(doc.id); setError(""); setNotice("");
    try {await removePolicyDocument(doc.id); await refresh(); setAnswer(null); setNotice("Policy removed.");}
    catch (err) {setError(err instanceof Error ? err.message : "Deletion failed");}
    finally {setDeleting("");}
  }
  async function ask(text: string) {
    const prompt=text.trim();
    if (prompt.length<3 || asking) return;
    setQuestion(prompt); setError(""); setNotice(""); setAnswer(null); setAsking(true);
    try {setAnswer(await askPolicies(prompt));}
    catch (err) {setError(err instanceof Error ? err.message : "Policy query failed");}
    finally {setAsking(false);}
  }
  const ready=documents.filter((d)=>d.status==="ready").length;
  return <main className="secure-workspace kb-workspace">
    <header className="secure-header">
      <div className="auth-brand"><span className="brandmark"><Sparkles size={18}/></span><strong>ResolveOps</strong></div>
      <nav className="headerlinks"><Link href="/workspace"><ArrowLeft size={15}/> Back to workspace</Link><span className="chip"><ShieldCheck size={12}/> Private policies</span></nav>
    </header>
    <div className="secure-intro"><div className="eyebrow">PHASE 3 · KNOWLEDGE & RAG</div><h1>Company Knowledge Base</h1><p className="muted">Upload policies and ask source-grounded questions using semantic search.</p></div>
    {error && <div className="notice error" role="alert">{error}</div>}
    {notice && <div className="notice" role="status">{notice}</div>}
    {loading ? <div className="notice"><Loader2 className="kb-spin" size={15}/> Loading your policies...</div> : <>
    <div className="kb-stats"><span><BookOpen size={17}/>{documents.length} documents</span><span><CheckCircle2 size={17}/>{ready} ready</span><span><ShieldCheck size={17}/> User-scoped RLS</span></div>
    <div className="kb-grid">
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Upload a policy</h2><p>PDF with text, TXT or Markdown · max 2 MB</p></div><UploadCloud size={20}/></div>
        <form className="stackform" onSubmit={(event)=>void onUpload(event)}>
          <label>Document<input ref={fileRef} type="file" accept=".pdf,.txt,.md" onChange={(event)=>chooseFile(event.target.files?.[0]??null)} required/></label>
          <label>Policy title<input value={title} maxLength={160} onChange={(event)=>setTitle(event.target.value)} placeholder="Returns and Refunds" required/></label>
          <button className="primarybtn" type="submit" disabled={!file || uploading}>{uploading ? <Loader2 size={15} className="kb-spin"/>:<UploadCloud size={15}/>} {uploading?"Indexing...":"Upload & index"}</button>
          <p className="muted kb-small">Text is sent to Google for embedding and answer generation. Original file bytes are not stored in Supabase; extracted chunks and vectors are retained.</p>
        </form>
        <div className="panelheader"><div><h2>Indexed policies</h2><p>Remove a policy to delete all its vectors</p></div><FileText size={17}/></div>
        <div className="secure-list kb-list">
          {documents.map((doc)=><div key={doc.id} className="kb-doc"><FileText size={17}/><div className="kb-doc-text"><strong>{doc.title}</strong><small>{doc.filename} · {doc.chunk_count} chunks · <b className={`kb-${doc.status}`}>{doc.status}</b></small>{doc.error_message && <small>{doc.error_message}</small>}</div>
            <button aria-label={`Delete ${doc.title}`} title={`Delete ${doc.title}`} className="kb-delete" type="button" disabled={deleting===doc.id} onClick={()=>void onDelete(doc)}><Trash2 size={16}/></button>
          </div>)}
          {documents.length===0 && <p className="muted">No policies yet. Upload a demo policy to get started.</p>}
        </div>
      </section>
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Ask your policies</h2><p>Answers include supporting citations and excerpts</p></div><Sparkles size={20}/></div>
        <form className="stackform" onSubmit={(e)=>{e.preventDefault();void ask(question);}}>
          <label>Question<textarea rows={3} maxLength={1000} value={question} onChange={(e)=>setQuestion(e.target.value)} placeholder="What is our return window?" required/></label>
          <button type="submit" className="primarybtn" disabled={asking || ready===0 || question.trim().length<3}>{asking?<Loader2 size={15} className="kb-spin"/>:<Send size={15}/>} {asking?"Searching policies...":"Ask knowledge base"}</button>
        </form>
        <div className="kb-examples">{examples.map((prompt)=><button className="prompt" type="button" key={prompt} disabled={asking||ready===0} onClick={()=>void ask(prompt)}>{prompt}</button>)}</div>
        {ready===0 && <p className="muted kb-small kb-empty">Upload at least one policy before asking questions.</p>}
        {answer && <div className="kb-answer" aria-live="polite"><div className="kb-answer-head"><strong>{answer.grounded?"Cited answer":"Not enough evidence"}</strong><span className={answer.grounded?"kb-ready":"kb-failed"}>{answer.grounded?"Grounded":"Unverified"}</span></div>
          <div className="kb-response">{answer.answer}</div><h3>Sources ({answer.sources.length})</h3>
          {answer.sources.map((source)=><article className="kb-source" key={source.citation}><strong>{source.citation} {source.title}</strong><small>{source.filename}{source.page_number ? ` · Page ${source.page_number}`:""} · Similarity {(source.similarity*100).toFixed(1)}%</small><blockquote>{source.excerpt}</blockquote></article>)}
        </div>}
      </section>
    </div></>}
    <footer className="infofooter">ResolveOps Phase 3 · Gemini 768-dimensional embeddings · pgvector cosine search · Human approval required for any refund.</footer>
  </main>;
}

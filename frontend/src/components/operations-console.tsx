"use client";
import {useCallback,useEffect,useState,type FormEvent} from "react";
import Link from "next/link";
import {useRouter} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {listTickets,type Ticket} from "@/lib/workspace-api";
import {listRuns,investigate,listApprovals,createApproval,decide,listAudit,getAnalytics,
  type Run,type Approval,type Audit,type Analytics} from "@/lib/operations-api";

type Tab="investigations"|"approvals"|"analytics"|"audit";
export default function OperationsConsole({initialTab="investigations"}:{initialTab?:Tab}){
  const router=useRouter();
  const [tab,setTab]=useState<Tab>(initialTab);
  const [tickets,setTickets]=useState<Ticket[]>([]);
  const [runs,setRuns]=useState<Run[]>([]);
  const [approvals,setApprovals]=useState<Approval[]>([]);
  const [audit,setAudit]=useState<Audit[]>([]);
  const [stats,setStats]=useState<Analytics|null>(null);
  const [current,setCurrent]=useState<Run|null>(null);
  const [ticketId,setTicketId]=useState("");
  const [question,setQuestion]=useState("");
  const [draft,setDraft]=useState("");
  const [reason,setReason]=useState("Human review required for this internal action.");
  const [kind,setKind]=useState<Approval["action_type"]>("send_reply");
  const [loading,setLoading]=useState(true);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [notice,setNotice]=useState("");

  const reload=useCallback(async()=>{
    const [t,r,a,h,s]=await Promise.all([listTickets(),listRuns(),listApprovals(),listAudit(),getAnalytics()]);
    setTickets(t.items);setRuns(r.items);setApprovals(a.items);setAudit(h.items);setStats(s);
  },[]);
  useEffect(()=>{
    let active=true;
    async function load(){
      const client=getSupabase();
      if(!client){if(active){setError("Missing Supabase public settings");setLoading(false);}return;}
      const {data,error:e}=await client.auth.getUser();
      if(!active)return;
      if(e||!data.user){router.replace("/login");return;}
      try{await reload();}catch(e){if(active)setError(e instanceof Error?e.message:"Load failed");}
      finally{if(active)setLoading(false);}
    }
    void load();
    return()=>{active=false};
  },[reload,router]);

  async function act(fn:()=>Promise<void>){
    setBusy(true);setError("");setNotice("");
    try{await fn();await reload();}catch(e){setError(e instanceof Error?e.message:"Request failed");}
    finally{setBusy(false);}
  }
  function start(e:FormEvent){
    e.preventDefault();if(!ticketId||question.trim().length<3)return;
    void act(async()=>{
      const result=await investigate(ticketId,question.trim());
      setCurrent(result.run);setDraft(result.run.response);
      setKind(result.suggested_action==="refund_review"?"refund_review":
              result.suggested_action==="resolve_ticket"?"resolve_ticket":"send_reply");
      setNotice("Investigation saved. Review the draft before acting.");
    });
  }
  function request(e:FormEvent){
    e.preventDefault();if(!current)return;
    void act(async()=>{
      await createApproval({ticket_id:current.ticket_id,
        run_id:current.requires_approval?current.id:undefined,
        action_type:kind,draft_reply:draft,reason});
      setNotice("Approval requested; no external email or refund has occurred.");setTab("approvals");
    });
  }
  function decision(item:Approval,value:"approved"|"rejected"){
    if(!window.confirm("Record "+value+" decision? This is an internal action only."))return;
    void act(async()=>{await decide(item.id,value);setNotice("Decision recorded in audit history.");});
  }
  return <main className="ops-root">
    <header className="ops-nav"><Link href="/workspace">✦ ResolveOps / Operations</Link><nav>
      <Link href="/workspace">Tickets</Link><Link href="/knowledge">Knowledge</Link>
      <Link href="/settings">Settings</Link></nav></header>
    <div className="ops-heading"><span>LANGGRAPH · HUMAN-IN-THE-LOOP</span>
      <h1>Resolution Center</h1><p>Investigate orders, retrieve policy evidence and approve internal actions.</p></div>
    <div className="ops-metrics">
      <div>Tickets <strong>{stats?.tickets??"–"}</strong></div>
      <div>Investigations <strong>{stats?.investigations??"–"}</strong></div>
      <div>Pending approvals <strong>{stats?.pending_approvals??"–"}</strong></div>
      <div>Avg. investigation <strong>{stats?stats.avg_run_ms+" ms":"–"}</strong></div>
    </div>
    {error&&<div className="ops-error" role="alert">{error}</div>}
    {notice&&<div className="ops-notice" role="status">{notice}</div>}
    <div className="ops-tabs" role="tablist">
      {(["investigations","approvals","analytics","audit"] as Tab[]).map(t=>
        <button role="tab" aria-selected={tab===t} key={t} type="button"
          className={tab===t?"selected":""} onClick={()=>setTab(t)}>{t}</button>)}
      <button type="button" onClick={()=>void act(async()=>{})} disabled={busy||loading}>Refresh</button>
    </div>
    {loading&&<section className="ops-panel">Loading your private workspace...</section>}
    {!loading&&tab==="investigations"&&<div className="ops-columns">
      <section className="ops-panel"><h2>Investigate a ticket</h2>
        <form className="ops-form" onSubmit={start}>
          <label>Ticket<select required value={ticketId} onChange={e=>setTicketId(e.target.value)}>
            <option value="">Choose ticket</option>
            {tickets.map(t=><option key={t.id} value={t.id}>{t.subject} ({t.status})</option>)}
          </select></label>
          <label>Customer problem<textarea required minLength={3} maxLength={1500}
            rows={5} value={question} onChange={e=>setQuestion(e.target.value)}
            placeholder="My order is delayed. Can I get a refund?"/></label>
          <button className="ops-primary" disabled={busy||!ticketId||question.trim().length<3}>Run LangGraph investigation</button>
        </form>
        <h3>Recent investigations</h3>
        {runs.length===0?<p>No investigations yet.</p>:runs.slice(0,12).map(r=>
          <button type="button" className="ops-record" key={r.id} onClick={()=>{
            setCurrent(r);setDraft(r.response);setKind("send_reply")}}>
            <b>{r.intent} — {tickets.find(t=>t.id===r.ticket_id)?.subject??"Ticket"}</b>
            <small>{r.status} · {r.duration_ms} ms</small>
          </button>)}
      </section>
      <section className="ops-panel"><h2>Draft and approval</h2>
        {!current?<p>Select or run an investigation to review the draft.</p>:<>
          <div className="ops-draft">{current.response}</div>
          {(current.review_flags?.length??0)>0&&
            <div className="ops-citation" role="status">
              <b>Human review flags</b>
              <ul>{current.review_flags?.map(flag=><li key={flag}>{flag.replaceAll("_"," ")}</li>)}</ul>
            </div>}
          {(current.workflow_steps?.length??0)>0&&
            <details className="ops-citation">
              <summary>Investigation workflow trace</summary>
              <ol>{current.workflow_steps?.map((step,index)=><li key={index}>{step}</li>)}</ol>
            </details>}
          {current.sources?.map((s,i)=><div className="ops-citation" key={i}>
            <b>{s.citation} {s.title}</b><p>{s.excerpt}</p></div>)}
          <form className="ops-form" onSubmit={request}>
            <label>Proposed action<select value={kind} onChange={e=>setKind(e.target.value as Approval["action_type"])}>
              <option value="send_reply">Record approved internal reply</option>
              <option value="resolve_ticket">Resolve ticket</option>
              <option value="refund_review">Review refund (no real payment)</option>
            </select></label>
            <label>Editable draft<textarea required maxLength={4000} rows={4}
              value={draft} onChange={e=>setDraft(e.target.value)}/></label>
            <label>Reason<textarea required minLength={3} maxLength={1000}
              value={reason} onChange={e=>setReason(e.target.value)}/></label>
            <button className="ops-primary" disabled={busy||draft.trim().length<1}>Request human approval</button>
          </form>
        </>}
      </section>
    </div>}
    {!loading&&tab==="approvals"&&<section className="ops-panel">
      <h2>Human approval queue</h2>
      {approvals.length===0?<p>No requests yet.</p>:approvals.map(a=>
        <article key={a.id} className="ops-approval">
          <div><b>{a.action_type.replaceAll("_"," ")} · {a.status}</b>
            <p>{a.draft_reply}</p><small>{a.reason}</small></div>
          {a.status==="pending"&&<div className="ops-actions">
            <button disabled={busy} onClick={()=>decision(a,"approved")}>Approve</button>
            <button disabled={busy} onClick={()=>decision(a,"rejected")}>Reject</button>
          </div>}
        </article>)}
    </section>}
    {!loading&&tab==="analytics"&&<div className="ops-columns">
      <section className="ops-panel"><h2>Ticket analytics</h2>
        <p>Open: {stats?.open_tickets??0}</p>
        <p>Resolved: {stats?.resolved_tickets??0}</p>
        <p>Approved internal actions: {stats?.approved_actions??0}</p>
      </section><section className="ops-panel"><h2>Safety metrics</h2>
        <p>Real refunds: {stats?.refunds_issued??0}</p>
        <p>Real external emails: {stats?.real_email_sent??0}</p>
        <p>{stats?.notice??"No external integrations."}</p>
      </section></div>}
    {!loading&&tab==="audit"&&<section className="ops-panel">
      <h2>Audit history</h2>
      {audit.length===0?<p>No decisions yet.</p>:audit.map(e=>
        <div className="ops-audit" key={e.id}>
          <b>{e.action_type.replaceAll("_"," ")} — {e.decision}</b>
          <span>{new Date(e.created_at).toLocaleString()}</span>
        </div>)}
    </section>}
    <footer className="ops-footer">No payment, real refund or customer email is executed by this portfolio demo.</footer>
  </main>
}

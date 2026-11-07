"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, Bot, CircleHelp, ClipboardList, Database, Headphones, LayoutDashboard, MessageSquare, Package, Send, ShieldCheck, Sparkles, TrendingUp } from "lucide-react";
import { fetchHealth, fetchOrders, sendMessage, type Health, type Order } from "@/lib/api";

type Message = { role: "assistant" | "user"; content: string; error?: boolean };
const suggestions = ["Where is order 1001?", "Check order 1002", "Is order 1003 delivered?"];
const welcome = "Welcome to ResolveOps. I can check fictional orders 1001, 1002 and 1003. All results are demo data. Ask me about an order to begin.";

export default function SupportWorkspace() {
  const [health, setHealth] = useState<Health | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: welcome }]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([fetchHealth(), fetchOrders()])
      .then(([status, data]) => { setHealth(status); setOrders(data.orders); setConnectionError(false); })
      .catch(() => setConnectionError(true));
  }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [messages]);

  async function submit(override?: string) {
    const prompt = (override ?? message).trim();
    if (!prompt || loading) return;
    setMessage("");
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setLoading(true);
    try {
      const result = await sendMessage(prompt);
      setMessages((prev) => [...prev, { role: "assistant", content: result.answer }]);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Unknown error";
      setMessages((prev) => [...prev, { role: "assistant", error: true, content: `Request failed: ${detail}. Check that FastAPI is running on port 8000.` }]);
    } finally { setLoading(false); }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brandmark"><Sparkles size={18}/></span>ResolveOps</div>
        <div>
          <div className="navlabel">WORKSPACE</div>
          <div className="navitem active"><LayoutDashboard size={17}/>Overview</div>
          <div className="navitem"><MessageSquare size={17}/>AI Assistant</div>
          <div className="navitem"><Package size={17}/>Orders</div>
          <Link className="navitem" href="/workspace"><ClipboardList size={17}/>Private Workspace</Link>
          <div className="navlabel" style={{marginTop:30}}>COMING NEXT</div>
          <div className="navitem"><Database size={17}/>Knowledge base</div>
          <div className="navitem"><ShieldCheck size={17}/>Approvals</div>
        </div>
        <div className="sidebarfoot"><h4><span className="statusdot"/>Phase 1 is ready</h4><p>Read-only sample orders. No real customer data, payments or refunds.</p></div>
      </aside>
      <main className="main">
        <div className="topbar">
          <div className="breadcrumbs"><Headphones size={15}/> Support workspace <ArrowRight size={13}/> Overview</div>
          <div className="avatars"><span className={`chip ${connectionError ? "warn" : ""}`}>{connectionError ? "API disconnected" : health ? `API online · ${health.agent_mode} mode` : "Checking API..."}</span><div className="avatar">AK</div></div>
        </div>
        <div className="headingrow">
          <div><div className="eyebrow">OPERATIONS OVERVIEW</div><h1>Support Command Center</h1><div className="muted">Investigate orders, test AI tools and prepare the next phase.</div></div>
          <Link className="chip" href="/login">Sign in to Phase 2</Link>
        </div>
        <div className="cards">
          <div className="card"><div className="cardtop"><span className="smalllabel">Demo orders</span><span className="iconbox"><Package size={16}/></span></div><div className="metric">{orders.length || "—"}</div><div className="metricmeta">Fictional records only</div></div>
          <div className="card"><div className="cardtop"><span className="smalllabel">Agent mode</span><span className="iconbox"><Bot size={16}/></span></div><div className="metric" style={{fontSize:22,textTransform:"capitalize"}}>{health?.agent_mode ?? "Offline"}</div><div className="metricmeta">Configured in backend/.env</div></div>
          <div className="card"><div className="cardtop"><span className="smalllabel">Tools available</span><span className="iconbox"><Activity size={16}/></span></div><div className="metric">01</div><div className="metricmeta">Read-only order lookup</div></div>
          <div className="card"><div className="cardtop"><span className="smalllabel">Refund actions</span><span className="iconbox"><ShieldCheck size={16}/></span></div><div className="metric">0</div><div className="metricmeta">Disabled for safety</div></div>
        </div>
        <div className="bodygrid">
          <section className="panel">
            <div className="panelheader"><div><h2>AI Support Console</h2><p>Ask a question about a fictional customer order</p></div><span className="chip"><Sparkles size={11} style={{verticalAlign:"middle",marginRight:5}}/>Assistant</span></div>
            <div className="chatlog" aria-live="polite">
              {messages.map((item, i) => <div className={`bubble ${item.role} ${item.error ? "error" : ""}`} key={i}><div className="messagelabel">{item.role === "assistant" ? "ResolveOps" : "You"}</div>{item.content}</div>)}
              {loading && <div className="bubble assistant">Checking order information...</div>}
              <div ref={bottomRef}/>
            </div>
            <div className="promptrow">{suggestions.map((s) => <button key={s} type="button" className="prompt" onClick={() => submit(s)} disabled={loading}>{s}</button>)}</div>
            <form className="composer" onSubmit={(e) => { e.preventDefault(); void submit(); }}><input aria-label="Message" value={message} maxLength={1500} onChange={(e) => setMessage(e.target.value)} placeholder="Ask about order 1001..."/><button className="primarybtn" type="submit" disabled={loading || !message.trim()}><Send size={14}/> Send</button></form>
          </section>
          <section className="panel">
            <div className="panelheader"><div><h2>Recent orders</h2><p>Sample order database</p></div><span className="iconbox"><TrendingUp size={16}/></span></div>
            <div className="tablehead"><span>ORDER</span><span>ITEM</span><span style={{textAlign:"center"}}>STATUS</span></div>
            {orders.length === 0 && <div className="emptyorders">{connectionError ? "Start the backend to load orders." : "Loading sample orders..."}</div>}
            {orders.map((order) => <div className="orderrow" key={order.order_id}><span className="ordernum">#{order.order_id}</span><span className="itemname" title={order.item}>{order.item}</span><span className={`orderstatus ${order.status.toLowerCase()}`}>{order.status}</span></div>)}
            <div className="footnote"><CircleHelp size={12} style={{verticalAlign:"middle",marginRight:6}}/>All orders are fabricated for learning. Future phases add authorized Supabase customer records.</div>
          </section>
        </div>
        <div className="infofooter">ResolveOps v0.1 · LangChain + FastAPI + Next.js · Phase 1 educational demo</div>
      </main>
    </div>
  );
}

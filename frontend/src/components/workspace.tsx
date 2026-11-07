"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Database, LogOut, MessageSquare, Package, RefreshCcw, ShieldCheck, Sparkles, Users } from "lucide-react";
import { getSupabase } from "@/lib/supabase";
import {
  createCustomer, createOrder, createTicket, listCustomers, listOrders, listTickets,
  listMessages, addMessage, changeTicketStatus, getProfile,
  type Customer, type Order, type Ticket, type TicketMessage,
} from "@/lib/workspace-api";

export default function Workspace() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [name, setName] = useState("");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState("");
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [message, setMessage] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [orderCustomer, setOrderCustomer] = useState("");
  const [orderItem, setOrderItem] = useState("");
  const [ticketCustomer, setTicketCustomer] = useState("");
  const [ticketOrder, setTicketOrder] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("normal");

  const refresh = useCallback(async () => {
    const [profile, customersResponse, ordersResponse, ticketsResponse] = await Promise.all([
      getProfile(), listCustomers(), listOrders(), listTickets(),
    ]);
    setName(profile.profile.display_name);
    setCustomers(customersResponse.items);
    setOrders(ordersResponse.items);
    setTickets(ticketsResponse.items);
  }, []);

  useEffect(() => {
    let mounted = true;
    async function start() {
      const supabase = getSupabase();
      if (!supabase) { if (mounted) { setError("Supabase is not configured. Add environment values and restart Next.js."); setLoading(false); } return; }
      const { data, error: authError } = await supabase.auth.getUser();
      if (!data.user || authError) { router.replace("/login"); return; }
      try { await refresh(); } catch (e) { if (mounted) setError(e instanceof Error ? e.message : "Could not load workspace"); }
      finally { if (mounted) setLoading(false); }
    }
    void start();
    return () => { mounted = false; };
  }, [refresh, router]);

  useEffect(() => {
    if (!selectedTicket) return;
    let active = true;
    listMessages(selectedTicket).then(r => {if (active) setMessages(r.items);}).catch(e => {if(active) setError(e instanceof Error ? e.message : "Message load failed");});
    return () => {active=false;};
  }, [selectedTicket]);

  async function action(work: () => Promise<void>) {
    setBusy(true); setError(""); setNotice("");
    try { await work(); await refresh(); setNotice("Saved successfully."); }
    catch (e) { setError(e instanceof Error ? e.message : "Operation failed"); }
    finally { setBusy(false); }
  }

  function onCustomer(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void action(async () => { await createCustomer({full_name:customerName, email:customerEmail}); setCustomerName(""); setCustomerEmail(""); });
  }
  function onOrder(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void action(async () => { await createOrder({customer_id: orderCustomer, item:orderItem}); setOrderItem(""); });
  }
  function onTicket(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void action(async () => {
      await createTicket({customer_id:ticketCustomer, ...(ticketOrder ? {order_id:ticketOrder} : {}), subject, description, priority});
      setSubject("");setDescription("");setTicketOrder("");
    });
  }
  function onMessage(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedTicket || !message.trim()) return;
    void action(async () => {
      await addMessage(selectedTicket, message);
      setMessage("");
      const result = await listMessages(selectedTicket);
      setMessages(result.items);
    });
  }
  async function logout() {
    await getSupabase()?.auth.signOut();
    router.replace("/login");
  }

  return <main className="secure-workspace">
    <header className="secure-header"><div className="auth-brand"><span className="brandmark"><Sparkles size={17}/></span><b>ResolveOps</b><span className="chip">Secure workspace</span></div><div className="headerlinks"><Link href="/"><ArrowLeft size={15}/> Demo dashboard</Link><button type="button" onClick={()=>void logout()}><LogOut size={15}/> Sign out</button></div></header>
    <section className="secure-intro"><div className="eyebrow">CUSTOMER SUPPORT OPERATIONS</div><h1>{name ? `Welcome, ${name}` : "Private workspace"}</h1><p className="muted">Your customer data is protected by signed-in access and Postgres row-level security. Use synthetic sample data for testing.</p></section>
    {loading && <div className="notice" role="status">Loading your workspace...</div>}
    {error && <div className="notice error" role="alert">{error}</div>}
    {notice && <div className="notice" role="status">{notice}</div>}
    <section className="secure-metrics" aria-label="Workspace statistics">
      <div className="card"><Users size={20}/><span>Customers</span><b>{customers.length}</b></div>
      <div className="card"><Package size={20}/><span>Orders</span><b>{orders.length}</b></div>
      <div className="card"><MessageSquare size={20}/><span>Tickets</span><b>{tickets.length}</b></div>
      <div className="card"><ShieldCheck size={20}/><span>Open tickets</span><b>{tickets.filter(t=>t.status === "open" || t.status === "in_progress").length}</b></div>
    </section>
    <div className="secure-grid">
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Customers</h2><p>Create your first customer</p></div><Users size={18}/></div>
        <form className="stackform" onSubmit={onCustomer}><label>Name<input value={customerName} onChange={e=>setCustomerName(e.target.value)} placeholder="Demo Customer" required minLength={2} maxLength={120}/></label><label>Email<input type="email" value={customerEmail} onChange={e=>setCustomerEmail(e.target.value)} placeholder="customer@example.com" required/></label><button className="primarybtn" disabled={busy} type="submit">Add customer</button></form>
        <div className="secure-list">{customers.map(c=><div key={c.id} className="secure-list-row"><strong>{c.full_name}</strong><span>{c.email}</span></div>)}{customers.length===0 && <p className="muted">No customers yet.</p>}</div>
      </section>
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Orders</h2><p>Track orders for your customers</p></div><Package size={18}/></div>
        <form className="stackform" onSubmit={onOrder}><label>Customer<select value={orderCustomer} onChange={e=>setOrderCustomer(e.target.value)} required><option value="">Choose customer</option>{customers.map(c=><option key={c.id} value={c.id}>{c.full_name}</option>)}</select></label><label>Item<input value={orderItem} onChange={e=>setOrderItem(e.target.value)} placeholder="Wireless Headphones" minLength={2} maxLength={200} required/></label><button className="primarybtn" disabled={busy || customers.length===0} type="submit">Add order</button></form>
        <div className="secure-list">{orders.map(o=><div key={o.id} className="secure-list-row"><strong>{o.item}</strong><span>{o.status} · {customers.find(c=>c.id===o.customer_id)?.full_name ?? "Customer"}</span></div>)}{orders.length===0 && <p className="muted">No orders yet.</p>}</div>
      </section>
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Support tickets</h2><p>Create and manage support cases</p></div><Database size={18}/></div>
        <form className="stackform" onSubmit={onTicket}>
          <label>Customer<select value={ticketCustomer} onChange={e=>{setTicketCustomer(e.target.value);setTicketOrder("");}} required><option value="">Choose customer</option>{customers.map(c=><option key={c.id} value={c.id}>{c.full_name}</option>)}</select></label>
          <label>Related order (optional)<select value={ticketOrder} onChange={e=>setTicketOrder(e.target.value)}><option value="">No order</option>{orders.filter(o=>o.customer_id===ticketCustomer).map(o=><option key={o.id} value={o.id}>{o.item}</option>)}</select></label>
          <label>Subject<input value={subject} onChange={e=>setSubject(e.target.value)} placeholder="Package hasn't arrived" required minLength={3} maxLength={200}/></label>
          <label>Description<textarea rows={3} value={description} onChange={e=>setDescription(e.target.value)} placeholder="Describe the customer's problem..." required minLength={3} maxLength={4000}/></label>
          <label>Priority<select value={priority} onChange={e=>setPriority(e.target.value)}><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select></label>
          <button className="primarybtn" disabled={busy || customers.length===0} type="submit">Create ticket</button>
        </form>
        <div className="secure-list">{tickets.map(t=><div key={t.id} className="secure-list-row ticket-row"><button type="button" onClick={()=>{setSelectedTicket(t.id);setMessages([]);}} className={selectedTicket===t.id ? "selected" : ""}><strong>{t.subject}</strong><small>{t.status.replace("_"," ")} · {t.priority}</small></button><select aria-label={`Status for ${t.subject}`} value={t.status} disabled={busy} onChange={e=>void action(async()=>{await changeTicketStatus(t.id,e.target.value);})}><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></div>)}{tickets.length===0 && <p className="muted">No tickets yet.</p>}</div>
      </section>
      <section className="panel secure-panel"><div className="panelheader"><div><h2>Ticket conversation</h2><p>Internal agent notes for selected ticket</p></div><MessageSquare size={18}/></div>
        {!selectedTicket && <p className="muted secure-tip">Select a support ticket to view or add its messages.</p>}
        {selectedTicket && <><div className="secure-list message-list">{messages.map(m=><div className="secure-list-row" key={m.id}><strong>Agent · {new Date(m.created_at).toLocaleString()}</strong><span>{m.content}</span></div>)}{messages.length===0 && <p className="muted">No messages yet.</p>}</div><form className="stackform" onSubmit={onMessage}><label>Message<textarea value={message} rows={3} maxLength={4000} onChange={e=>setMessage(e.target.value)} placeholder="Write an internal agent note..." required/></label><button type="submit" className="primarybtn" disabled={busy || !message.trim()}>Add note</button></form></>}
      </section>
    </div>
    <footer className="infofooter"><RefreshCcw size={12}/> Phase 2 · Authenticated CRUD over Supabase · Tickets and order updates are manual; AI actions are planned for later phases.</footer>
  </main>;
}

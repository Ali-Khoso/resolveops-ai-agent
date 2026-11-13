"use client";
import {useMemo,useState} from "react";
import {ArrowRight, ChevronLeft, ChevronRight, Filter, Search, Ticket, X} from "lucide-react";
import Link from "next/link";
import type {Customer,Order,Ticket as TicketRecord} from "@/lib/workspace-api";
import {filterTickets,pageCount,type TicketFilter} from "@/lib/phase6-tickets";

const PAGE_SIZE=7;
export default function TicketExplorer({tickets,customers,orders}:{
  tickets:TicketRecord[];customers:Customer[];orders:Order[];
}){
  const [filter,setFilter]=useState<TicketFilter>({query:"",status:"all",priority:"all",sort:"newest"});
  const [page,setPage]=useState(1);
  const [selectedId,setSelectedId]=useState<string|null>(null);
  const visible=useMemo(()=>filterTickets(tickets,customers,filter),[tickets,customers,filter]);
  const pages=pageCount(visible.length,PAGE_SIZE);
  const safePage=Math.min(page,pages);
  const displayed=visible.slice((safePage-1)*PAGE_SIZE,safePage*PAGE_SIZE);
  const selected=tickets.find(t=>t.id===selectedId);
  const customer=selected?customers.find(c=>c.id===selected.customer_id):null;
  const order=selected?.order_id?orders.find(o=>o.id===selected.order_id):null;
  function update(next:Partial<TicketFilter>){setFilter(p=>({...p,...next}));setPage(1);}
  return <div className="p6-panel p6-explorer">
    <div className="p6-explorer-toolbar">
      <label className="p6-search"><Search size={17}/><span className="p6-sr-only">Search tickets</span>
        <input value={filter.query} onChange={e=>update({query:e.target.value})} placeholder="Search subject, description, customer or ID..." type="search"/></label>
      <div className="p6-filter-pair"><Filter size={15} aria-hidden="true"/>
        <label><span className="p6-sr-only">Ticket status</span><select value={filter.status} onChange={e=>update({status:e.target.value})}>
          <option value="all">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="resolved">Resolved</option><option value="closed">Closed</option>
        </select></label>
        <label><span className="p6-sr-only">Ticket priority</span><select value={filter.priority} onChange={e=>update({priority:e.target.value})}>
          <option value="all">All priorities</option><option value="urgent">Urgent</option><option value="high">High</option><option value="normal">Normal</option><option value="low">Low</option>
        </select></label>
        <label><span className="p6-sr-only">Sort tickets</span><select value={filter.sort} onChange={e=>update({sort:e.target.value as TicketFilter["sort"]})}>
          <option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="priority">Priority first</option>
        </select></label>
      </div>
    </div>
    <div className="p6-table-wrap"><table className="p6-table">
      <thead><tr><th>Ticket / subject</th><th>Customer</th><th>Priority</th><th>Status</th><th>Created</th><th><span className="p6-sr-only">Details</span></th></tr></thead>
      <tbody>{displayed.map(t=><tr key={t.id}>
        <td><button className="p6-row-button" onClick={()=>setSelectedId(t.id)}><span className="p6-table-ticket-icon"><Ticket size={16}/></span><span><strong>{t.subject}</strong><small>#{t.id.slice(0,8)}</small></span></button></td>
        <td>{customers.find(c=>c.id===t.customer_id)?.full_name??"Unknown customer"}</td>
        <td><span className={"p6-priority p6-priority-"+t.priority}><span/> {t.priority}</span></td>
        <td><span className={"p6-pill p6-pill-"+t.status}>{t.status.replaceAll("_"," ")}</span></td>
        <td>{new Date(t.created_at).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})}</td>
        <td><button className="p6-table-open" aria-label={`View ${t.subject}`} onClick={()=>setSelectedId(t.id)}><ChevronRight size={16}/></button></td>
      </tr>)}</tbody>
    </table></div>
    {!visible.length&&<div className="p6-empty">No tickets match your filters. Try clearing your search.</div>}
    <div className="p6-pager"><span>Showing {visible.length?((safePage-1)*PAGE_SIZE+1):0}–{Math.min(safePage*PAGE_SIZE,visible.length)} of {visible.length} matching tickets</span>
      <div><button aria-label="Previous page" disabled={safePage===1} onClick={()=>setPage(n=>Math.max(1,n-1))}><ChevronLeft size={15}/></button><span>Page {safePage} of {pages}</span><button aria-label="Next page" disabled={safePage===pages} onClick={()=>setPage(n=>Math.min(pages,n+1))}><ChevronRight size={15}/></button></div>
    </div>
    {selected&&<div className="p6-detail-backdrop" onClick={()=>setSelectedId(null)}>
      <aside className="p6-detail-panel" aria-label="Ticket details" role="dialog" aria-modal="true" onClick={e=>e.stopPropagation()}>
        <div className="p6-detail-title"><div><small>TICKET DETAILS</small><h2>{selected.subject}</h2></div><button aria-label="Close ticket details" onClick={()=>setSelectedId(null)}><X size={18}/></button></div>
        <div className="p6-detail-tags"><span className={"p6-pill p6-pill-"+selected.status}>{selected.status.replaceAll("_"," ")}</span><span className={"p6-priority p6-priority-"+selected.priority}>{selected.priority}</span></div>
        <h3>Customer request</h3><p className="p6-detail-description">{selected.description}</p>
        <h3>Customer</h3><p>{customer?.full_name??"Unknown"}<br/><small>{customer?.email??"No email available"}</small></p>
        <h3>Linked order</h3><p>{order?order.item:"No linked order"}<br/><small>{order?.tracking_number??"No tracking number"}</small></p>
        <div className="p6-detail-actions"><Link className="p6-button" href="/operations">Investigate with AI <ArrowRight size={14}/></Link><Link className="p6-button p6-button-secondary" href="/workspace">Edit in workspace</Link></div>
      </aside>
    </div>}
  </div>;
}

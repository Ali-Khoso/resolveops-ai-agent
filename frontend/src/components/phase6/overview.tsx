import Link from "next/link";
import { ArrowRight, ArrowUpRight, CheckCheck, ChevronRight, Clock3, Headset, ShieldCheck, Sparkles, Ticket, Workflow } from "lucide-react";
import type { Ticket as TicketRecord } from "@/lib/workspace-api";
import type { Analytics, Approval, Run } from "@/lib/operations-api";

export type OverviewData = {tickets:TicketRecord[];approvals:Approval[];runs:Run[];stats:Analytics};

function Status({status}:{status:string}){
  return <span className={"p6-pill p6-pill-"+status.replace(/[^a-z_]/gi,"").toLowerCase()}>{status.replaceAll("_"," ")}</span>;
}
const palettes=["#b2e37b","#8b9dff","#f7c28a","#7687a4"] as const;

export default function Overview({data}:{data:OverviewData}){
  const {tickets,approvals,runs,stats}=data;
  const pending=approvals.filter(x=>x.status==="pending");
  const buckets=[
    {title:"Open",value:tickets.filter(x=>x.status==="open").length},
    {title:"In progress",value:tickets.filter(x=>x.status==="in_progress").length},
    {title:"Resolved",value:tickets.filter(x=>x.status==="resolved").length},
    {title:"Closed",value:tickets.filter(x=>x.status==="closed").length}
  ];
  const total=tickets.length||1;
  return <>
    <section className="p6-kpi-grid" aria-label="Workspace metrics">
      {[
        {name:"Total tickets",value:stats.tickets,caption:"Visible workspace records",icon:Ticket,accent:"green"},
        {name:"Open tickets",value:stats.open_tickets,caption:"Open and in progress",icon:Headset,accent:"blue"},
        {name:"AI investigations",value:stats.investigations,caption:"Saved investigation runs",icon:Sparkles,accent:"purple"},
        {name:"Pending reviews",value:stats.pending_approvals,caption:"Awaiting human decision",icon:ShieldCheck,accent:"orange"},
      ].map(item=><div className={"p6-kpi p6-panel p6-kpi-"+item.accent} key={item.name}>
        <div className="p6-kpi-top"><span>{item.name}</span><item.icon size={18}/></div>
        <strong>{item.value.toLocaleString()}</strong><p>{item.caption}</p></div>)}
    </section>
    <div className="p6-feature-grid">
      <section className="p6-panel p6-panel-pad p6-distribution">
        <div className="p6-section-head"><div><h2 className="p6-panel-title">Ticket health</h2><p className="p6-panel-caption">Current status distribution · {tickets.length} visible tickets</p></div><Link href="/tickets" className="p6-text-link">View all <ArrowUpRight size={14}/></Link></div>
        <div className="p6-segment-bar" aria-label="Distribution of ticket statuses">
          {buckets.map((b,i)=><span key={b.title} style={{width:`${b.value/total*100}%`,background:palettes[i]}}/>)}
        </div>
        <div className="p6-bars">{buckets.map((bucket,i)=><div className="p6-bar-line" key={bucket.title}>
          <div className="p6-bar-text"><span><i style={{background:palettes[i]}}/>{bucket.title}</span><b>{bucket.value}</b></div>
          <div className="p6-bar-track"><span style={{width:`${bucket.value/total*100}%`,background:palettes[i]}}/></div></div>)}</div>
        <p className="p6-footnote">Counts reflect the currently loaded records, not a historical trend.</p>
      </section>
      <section className="p6-panel p6-panel-pad p6-review-card">
        <div className="p6-section-head"><div><h2 className="p6-panel-title">Human review queue</h2><p className="p6-panel-caption">Actions always need your approval</p></div><span className="p6-count-bubble">{pending.length}</span></div>
        <div className="p6-review-list">{pending.slice(0,4).map((item,i)=><div key={item.id} className="p6-review-row">
          <span className="p6-review-icon"><ShieldCheck size={16}/></span><div><strong>{item.action_type.replaceAll("_"," ")}</strong><small>{item.reason}</small></div><span className="p6-review-order">{String(i+1).padStart(2,"0")}</span></div>)}
          {!pending.length&&<div className="p6-empty"><CheckCheck size={19}/> No pending approvals</div>}
        </div>
        <Link className="p6-inline-button" href="/operations">Review pending actions <ArrowRight size={15}/></Link>
      </section>
    </div>
    <div className="p6-feature-grid p6-feature-bottom">
      <section className="p6-panel p6-panel-pad">
        <div className="p6-section-head"><div><h2 className="p6-panel-title">Latest support tickets</h2><p className="p6-panel-caption">Recently created customer requests</p></div><Link className="p6-text-link" href="/tickets">All tickets <ArrowUpRight size={14}/></Link></div>
        <div className="p6-ticket-list">{tickets.slice(0,5).map(x=><Link href="/tickets" className="p6-ticket-line" key={x.id}>
          <div className="p6-ticket-symbol"><Ticket size={15}/></div><div className="p6-ticket-name"><strong>{x.subject}</strong><small>{x.priority} priority · {new Date(x.created_at).toLocaleDateString("en-US",{month:"short",day:"numeric"})}</small></div>
          <Status status={x.status}/><ChevronRight size={15} className="p6-chevron"/></Link>)}
          {!tickets.length&&<div className="p6-empty">No tickets created yet. Start in the Tickets workspace.</div>}</div>
      </section>
      <section className="p6-panel p6-panel-pad">
        <div className="p6-section-head"><div><h2 className="p6-panel-title">Recent AI investigations</h2><p className="p6-panel-caption">Decision support · not autonomous actions</p></div><Workflow size={19} className="p6-panel-icon"/></div>
        <div className="p6-investigation-list">{runs.slice(0,4).map(run=><div className="p6-investigation-row" key={run.id}>
          <span className="p6-run-icon"><Sparkles size={15}/></span><div><strong>{run.intent.replaceAll("_"," ")} investigation</strong><small>{run.question}</small></div><span>{Math.max(0,Math.round(run.duration_ms/1000))}s</span></div>)}
          {!runs.length&&<div className="p6-empty">No saved investigations. Run one from Agent operations.</div>}</div>
        <Link href="/operations" className="p6-text-link p6-investigation-link"><Clock3 size={14}/> Open investigations <ArrowRight size={14}/></Link>
      </section>
    </div>
  </>;
}

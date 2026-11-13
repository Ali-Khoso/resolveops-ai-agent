import {Activity,BarChart3,Clock3,ShieldCheck,TriangleAlert} from "lucide-react";
import type {OverviewData} from "@/components/phase6/overview";
const COLORS=["#b2e37b","#91a9fc","#efc28c","#9a9eb5"];

export default function Insights({data}:{data:OverviewData}){
  const {tickets,approvals,runs,stats}=data;
  const priorities=["urgent","high","normal","low"].map(name=>({name,value:tickets.filter(t=>t.priority===name).length}));
  const states=["open","in_progress","resolved","closed"].map(name=>({name,value:tickets.filter(t=>t.status===name).length}));
  const approvalStates=["pending","approved","rejected"].map(name=>({name,value:approvals.filter(a=>a.status===name).length}));
  const total=Math.max(1,tickets.length), maxPriority=Math.max(1,...priorities.map(x=>x.value));
  return <>
    <div className="p6-insights-hero p6-panel">
      <div><p className="p6-eyebrow">OPERATIONS SNAPSHOT</p><h2>Know where your queue stands.</h2>
        <p>Live counts from the currently loaded private workspace. This is a snapshot, not a forecast or historical trend.</p></div>
      <BarChart3 size={78} strokeWidth={1.15} aria-hidden="true"/>
    </div>
    <div className="p6-quick-stats">
      {[{label:"Tracked tickets",value:stats.tickets,icon:Activity},
        {label:"Agent investigations",value:stats.investigations,icon:BarChart3},
        {label:"Awaiting approval",value:stats.pending_approvals,icon:ShieldCheck},
        {label:"Average run duration",value:stats.avg_run_ms+" ms",icon:Clock3}
      ].map(x=><div key={x.label} className="p6-panel p6-stat"><x.icon size={16}/><span>{x.label}</span><strong>{x.value}</strong></div>)}
    </div>
    <div className="p6-analytics-grid">
      <section className="p6-panel p6-panel-pad"><h2 className="p6-panel-title">Ticket status mix</h2><p className="p6-panel-caption">Distribution of {tickets.length} listed tickets</p>
        <div className="p6-ring-wrap"><div className="p6-ring" role="img" aria-label="Ticket status proportions"
          style={{background:`conic-gradient(${states.map((s,i)=>`${COLORS[i]} ${states.slice(0,i).reduce((a,b)=>a+b.value,0)/total*100}% ${states.slice(0,i+1).reduce((a,b)=>a+b.value,0)/total*100}%`).join(",")})`}}>
          <div><strong>{tickets.length}</strong><span>tickets</span></div></div>
          <div className="p6-ring-legend">{states.map((x,i)=><div key={x.name}><span><i style={{background:COLORS[i]}}/>{x.name.replaceAll("_"," ")}</span><b>{x.value}</b></div>)}</div>
        </div></section>
      <section className="p6-panel p6-panel-pad"><h2 className="p6-panel-title">Priority distribution</h2><p className="p6-panel-caption">Where attention may be needed first</p>
        <div className="p6-chart-bars">{priorities.map((x,i)=><div className="p6-chart-line" key={x.name}><span>{x.name}</span><div><span style={{width:`${x.value/maxPriority*100}%`,background:COLORS[i]}}/></div><b>{x.value}</b></div>)}</div>
      </section>
      <section className="p6-panel p6-panel-pad"><h2 className="p6-panel-title">Approval outcomes</h2><p className="p6-panel-caption">Within the loaded review queue</p>
        <div className="p6-approval-stats">{approvalStates.map(x=><div key={x.name}><span className={"p6-pill p6-pill-"+x.name}>{x.name}</span><strong>{x.value}</strong></div>)}</div></section>
      <section className="p6-panel p6-panel-pad"><h2 className="p6-panel-title">Automation boundaries</h2><p className="p6-panel-caption">Safety properties of this portfolio implementation</p>
        <div className="p6-safe-note"><TriangleAlert size={20}/><p>Approvals create internal records or resolve tickets. They do not issue real refunds or send customer emails.</p></div>
        <div className="p6-safe-stats"><span>Real payments issued <strong>0</strong></span><span>Outbound emails sent <strong>0</strong></span></div>
      </section>
    </div>
    <p className="p6-footnote">Dashboard totals are capped by backend collection limits. For production reporting, use server-side aggregate queries and consistent pagination.</p>
  </>;
}

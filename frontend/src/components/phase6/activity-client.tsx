"use client";
import {useCallback,useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {Activity,CheckCircle2,Clock3,RotateCcw,ShieldCheck,Sparkles} from "lucide-react";
import Phase6Shell from "@/components/phase6/shell";
import {getSupabase} from "@/lib/supabase";
import {listAudit,listRuns,type Audit,type Run} from "@/lib/operations-api";

export default function ActivityClient(){
  const router=useRouter();
  const [audit,setAudit]=useState<Audit[]>([]);
  const [runs,setRuns]=useState<Run[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const refresh=useCallback(async()=>{
    setLoading(true);setError("");
    try{
      const [a,r]=await Promise.all([listAudit(undefined,50),listRuns()]);
      setAudit(a.items);setRuns(r.items);
    }catch(e){setError(e instanceof Error?e.message:"Could not load activity.");}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{
    let active=true;
    (async()=>{
      const sb=getSupabase();
      if(!sb){if(active){setError("Configure Supabase before loading activity.");setLoading(false);}return;}
      const {data,error:err}=await sb.auth.getUser();
      if(!active)return;
      if(err||!data.user){router.replace("/login");return;}
      await refresh();
    })();
    return()=>{active=false;};
  },[router,refresh]);
  const events=[
    ...audit.map(item=>({id:"audit-"+item.id,at:item.created_at,
      label:`${item.decision} ${item.action_type.replaceAll("_"," ")}`,
      detail:"Human decision recorded in internal audit history",kind:"decision" as const})),
    ...runs.map(item=>({id:"run-"+item.id,at:item.created_at,
      label:`${item.intent} investigation saved`,
      detail:item.question,kind:"agent" as const}))
  ].sort((a,b)=>b.at.localeCompare(a.at)).slice(0,50);
  return <Phase6Shell active="/activity" eyebrow="REVIEW HISTORY" title="Workspace activity"
    description="An account-scoped view of recent AI investigations and human review decisions."
    actions={<button className="p6-button p6-button-secondary" disabled={loading} onClick={()=>void refresh()}><RotateCcw size={14}/> Refresh</button>}>
    {error&&<p className="p6-alert" role="alert">{error}</p>}
    <section className="p6-panel p6-panel-pad">
      <div className="p6-section-head"><div><h2 className="p6-panel-title">Recent activity</h2>
        <p className="p6-panel-caption">Latest 50 merged events from two capped sources</p></div><Activity size={18} className="p6-panel-icon"/></div>
      {loading?<div className="p6-loading"><div className="p6-skeleton"/><div className="p6-skeleton"/></div>:events.length?events.map(event=><div className="p6-timeline-event" key={event.id}>
        <div className={"p6-timeline-icon "+(event.kind==="decision"?"p6-timeline-review":"p6-timeline-agent")}>
          {event.kind==="decision"?<ShieldCheck size={18}/>:<Sparkles size={18}/>}</div>
        <div><h3>{event.label}</h3><p>{event.detail}</p></div>
        <time dateTime={event.at}><Clock3 size={12}/>{new Date(event.at).toLocaleString()}</time>
      </div>):<div className="p6-empty"><CheckCircle2 size={19}/>No recent activity in this workspace.</div>}
    </section>
  </Phase6Shell>;
}

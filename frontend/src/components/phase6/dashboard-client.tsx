"use client";
import {useCallback,useEffect,useState} from "react";
import Link from "next/link";
import {ArrowRight, RotateCcw, ShieldAlert, TicketPlus} from "lucide-react";
import {useRouter} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {listTickets} from "@/lib/workspace-api";
import {getAnalytics,listApprovals,listRuns} from "@/lib/operations-api";
import Phase6Shell from "@/components/phase6/shell";
import Overview,{type OverviewData} from "@/components/phase6/overview";

async function loadOverview():Promise<OverviewData>{
  const [tickets,approvals,runs,stats]=await Promise.all([
    listTickets(),listApprovals("all",50),listRuns(),getAnalytics()
  ]);
  return {tickets:tickets.items,approvals:approvals.items,runs:runs.items,stats};
}

export default function DashboardClient(){
  const router=useRouter();
  const [data,setData]=useState<OverviewData|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(true);
  const refresh=useCallback(async()=>{
    setLoading(true);setError("");
    try{setData(await loadOverview());}
    catch(exc){setError(exc instanceof Error?exc.message:"Could not load your workspace.");}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{
    let alive=true;
    (async()=>{
      const sb=getSupabase();
      if(!sb){if(alive){setError("Add your Supabase public environment variables to frontend/.env.local.");setLoading(false);}return;}
      const {data:auth,error:authError}=await sb.auth.getUser();
      if(!alive)return;
      if(authError||!auth.user){router.replace("/login");return;}
      await refresh();
    })();
    return()=>{alive=false;};
  },[refresh,router]);
  return <Phase6Shell active="/dashboard" eyebrow="YOUR CONTROL CENTER" title="Workspace overview"
    description="Every ticket, investigation and human review in one clear place."
    actions={<><button className="p6-button p6-button-secondary" onClick={()=>void refresh()} disabled={loading}><RotateCcw size={14}/> Refresh</button><Link className="p6-button" href="/workspace"><TicketPlus size={15}/> New support ticket <ArrowRight size={14}/></Link></>}>
    {error&&<div className="p6-alert" role="alert"><ShieldAlert size={16}/> {error} <button className="p6-button p6-button-secondary" onClick={()=>void refresh()}>Retry</button></div>}
    {loading?<div className="p6-loading" role="status" aria-live="polite"><div className="p6-kpi-grid">{[1,2,3,4].map(i=><div key={i} className="p6-skeleton"/>)}</div><div className="p6-skeleton"/><div className="p6-skeleton"/></div>:
      data?<Overview data={data}/>:<div className="p6-empty">Your workspace could not be loaded. Check credentials and retry.</div>}
  </Phase6Shell>;
}

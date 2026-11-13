"use client";
import {useCallback,useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import {RotateCcw} from "lucide-react";
import {getSupabase} from "@/lib/supabase";
import {listTickets} from "@/lib/workspace-api";
import {listApprovals,listRuns,getAnalytics} from "@/lib/operations-api";
import Phase6Shell from "@/components/phase6/shell";
import Insights from "@/components/phase6/insights";
import type {OverviewData} from "@/components/phase6/overview";
export default function InsightsClient(){
  const router=useRouter(),[data,setData]=useState<OverviewData|null>(null);
  const [loading,setLoading]=useState(true),[error,setError]=useState("");
  const refresh=useCallback(async()=>{
    setLoading(true);setError("");
    try{
      const [t,a,r,s]=await Promise.all([listTickets(),listApprovals("all",50),listRuns(),getAnalytics()]);
      setData({tickets:t.items,approvals:a.items,runs:r.items,stats:s});
    }catch(e){setError(e instanceof Error?e.message:"Unable to fetch analytics.");}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{
    let active=true;
    (async()=>{
      const sb=getSupabase();
      if(!sb){if(active){setError("Configure Supabase public environment variables.");setLoading(false);}return;}
      const {data:auth,error:err}=await sb.auth.getUser();
      if(!active)return;
      if(err||!auth.user){router.replace("/login");return;}
      await refresh();
    })();
    return()=>{active=false;};
  },[router,refresh]);
  return <Phase6Shell active="/insights" eyebrow="DATA YOU CAN TRUST" title="Operations insights" description="A snapshot of support workload, AI investigations and approval outcomes."
    actions={<button className="p6-button p6-button-secondary" disabled={loading} onClick={()=>void refresh()}><RotateCcw size={14}/> Refresh data</button>}>
    {error&&<p role="alert" className="p6-alert">{error}</p>}
    {loading?<div className="p6-loading"><div className="p6-skeleton"/><div className="p6-skeleton"/></div>:data?<Insights data={data}/>:<div className="p6-empty">No analytics available. Verify connection and retry.</div>}
  </Phase6Shell>;
}

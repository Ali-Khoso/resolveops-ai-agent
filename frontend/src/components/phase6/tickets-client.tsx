"use client";
import {useCallback,useEffect,useState} from "react";
import Link from "next/link";
import {ArrowRight,RotateCcw,TicketPlus} from "lucide-react";
import {useRouter} from "next/navigation";
import Phase6Shell from "@/components/phase6/shell";
import TicketExplorer from "@/components/phase6/ticket-explorer";
import {getSupabase} from "@/lib/supabase";
import {listTickets,listCustomers,listOrders,type Ticket,type Customer,type Order} from "@/lib/workspace-api";

type Records={tickets:Ticket[];customers:Customer[];orders:Order[]};
export default function TicketsClient(){
  const router=useRouter();
  const [records,setRecords]=useState<Records|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const refresh=useCallback(async()=>{
    setLoading(true);setError("");
    try{
      const [tickets,customers,orders]=await Promise.all([listTickets(),listCustomers(),listOrders()]);
      setRecords({tickets:tickets.items,customers:customers.items,orders:orders.items});
    }catch(exc){setError(exc instanceof Error?exc.message:"Could not load tickets.");}
    finally{setLoading(false);}
  },[]);
  useEffect(()=>{
    let alive=true;
    (async()=>{
      const sb=getSupabase();
      if(!sb){if(alive){setError("Configure frontend Supabase credentials.");setLoading(false);}return;}
      const {data,error:err}=await sb.auth.getUser();
      if(!alive)return;
      if(err||!data.user){router.replace("/login");return;}
      await refresh();
    })();
    return()=>{alive=false;};
  },[router,refresh]);
  return <Phase6Shell active="/tickets" eyebrow="SUPPORT INBOX" title="Ticket explorer"
    description="Find issues quickly, inspect related orders and start an AI investigation."
    actions={<><button className="p6-button p6-button-secondary" onClick={()=>void refresh()} disabled={loading}><RotateCcw size={14}/> Refresh</button><Link className="p6-button" href="/workspace"><TicketPlus size={15}/> Create ticket <ArrowRight size={14}/></Link></>}>
    {error&&<div className="p6-alert" role="alert">{error}</div>}
    {loading?<div className="p6-loading" role="status" aria-live="polite"><div className="p6-skeleton"/><div className="p6-skeleton"/><div className="p6-skeleton"/></div>:
      records?<TicketExplorer {...records}/>:<div className="p6-empty">Unable to load tickets. Verify your credentials and retry.</div>}
  </Phase6Shell>;
}

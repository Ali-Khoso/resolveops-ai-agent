import "../phase6.css";
import {ArrowUpRight} from "lucide-react";
import Link from "next/link";
import Phase6Shell from "@/components/phase6/shell";
import Overview from "@/components/phase6/overview";
import DemoTabs from "@/components/phase6/demo-tabs";
import {demoOverview} from "@/lib/phase6-demo";
export const metadata={title:"Phase 6 preview — ResolveOps",robots:{index:false,follow:false}};
export default function Showcase(){
 return <Phase6Shell active="/dashboard" eyebrow="EXPLORE THE EXPERIENCE" title="Workspace overview"
  description="Ticket triage, AI investigations and approvals in one beautiful workflow." demo
  actions={<Link href="/dashboard" className="p6-button">Open signed-in dashboard <ArrowUpRight size={14}/></Link>}>
  <DemoTabs/><Overview data={demoOverview}/>
 </Phase6Shell>;
}

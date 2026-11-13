import Link from "next/link";
import {ArrowUpRight,BookOpen,ShieldCheck,Workflow} from "lucide-react";
import "../phase6.css";
import Phase6Shell from "@/components/phase6/shell";
export default function DocsPage(){return <Phase6Shell active="/docs" eyebrow="START HERE" title="Help & documentation"
  description="Explore the workspace features and the safe workflow for internal support teams.">
  <div className="p6-docs-grid">
    {[{heading:"1. Create a ticket",description:"Open Tickets, select Create ticket, then add a customer, optionally link an order, and submit a support issue.",href:"/workspace",icon:BookOpen},
      {heading:"2. Investigate with AI",description:"Open Agent operations. Select a ticket, enter the question, and inspect the cited policy evidence and draft.",href:"/operations",icon:Workflow},
      {heading:"3. Review the proposed action",description:"Use the approvals tab to read the draft and provide a written decision. Refund review never triggers real payments.",href:"/operations",icon:ShieldCheck},
      {heading:"4. Monitor activity",description:"Use Analytics and Activity to inspect current ticket counts, saved investigations, and decisions.",href:"/insights",icon:ArrowUpRight}
    ].map(item=><div className="p6-panel p6-panel-pad" key={item.heading}><item.icon size={24} color="#b7e08e"/><h2 className="p6-panel-title">{item.heading}</h2><p>{item.description}</p><Link href={item.href} className="p6-text-link">Open feature <ArrowUpRight size={14}/></Link></div>)}
  </div>
  <div className="p6-panel p6-panel-pad" style={{marginTop:18}}><h2 className="p6-panel-title">Credentials & production safety</h2><p className="p6-panel-caption">Configure Supabase and Gemini with the repository's setup guide. Never commit .env files, real customer credentials, or service-role keys. This is a portfolio demonstration, not a production payment automation service.</p></div>
</Phase6Shell>;}
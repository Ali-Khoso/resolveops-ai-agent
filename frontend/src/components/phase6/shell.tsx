import Link from "next/link";
import { Activity, ArrowUpRight, BookOpenText, ChartNoAxesCombined, CircleHelp, ClipboardCheck, Command, LayoutDashboard, LifeBuoy, Settings2, TicketCheck, Workflow } from "lucide-react";
import type { ReactNode } from "react";

const links = [
  {href:"/dashboard",title:"Overview",icon:LayoutDashboard},
  {href:"/tickets",title:"Tickets",icon:TicketCheck},
  {href:"/operations",title:"Agent operations",icon:Workflow},
  {href:"/knowledge",title:"Knowledge base",icon:BookOpenText},
  {href:"/insights",title:"Analytics",icon:ChartNoAxesCombined},
  {href:"/activity",title:"Activity",icon:Activity},
];

export default function Phase6Shell({children,active,eyebrow,title,description,actions,demo=false}:{
  children:ReactNode;active:string;eyebrow:string;title:string;description:string;
  actions?:ReactNode;demo?:boolean;
}) {
  return <div className="p6-layout">
    <aside className="p6-sidebar">
      <Link className="p6-brand" href="/dashboard" aria-label="ResolveOps dashboard">
        <span className="p6-brand-mark"><Command size={20}/></span>
        <span>resolve<span className="p6-brand-accent">ops</span><small>AI OPERATIONS</small></span>
      </Link>
      <div className="p6-workspace-card">
        <span className="p6-workspace-orb">R</span><span><strong>ResolveOps workspace</strong><small>{demo?"Sample workspace":"Private support workspace"}</small></span>
        <span className="p6-workspace-chevron">⌄</span>
      </div>
      <p className="p6-nav-caption">WORKSPACE</p>
      <nav aria-label="Main navigation" className="p6-navigation">
        {links.map(item=><Link key={item.href} href={item.href} aria-current={active===item.href?"page":undefined} className={"p6-nav-link"+(active===item.href?" p6-active":"")}>
          <item.icon size={17} strokeWidth={1.9}/><span>{item.title}</span>{item.href==="/operations"&&<span className="p6-nav-dot"/>}
        </Link>)}
      </nav>
      <p className="p6-nav-caption p6-secondary-caption">SUPPORT</p>
      <nav className="p6-navigation" aria-label="Support navigation">
        <Link href="/settings" className="p6-nav-link"><Settings2 size={17}/>Settings</Link>
        <Link href="/docs" className="p6-nav-link"><CircleHelp size={17}/>Help & docs</Link>
      </nav>
      <div className="p6-sidebar-bottom">
        <div className="p6-assistant-card">
          <div className="p6-assistant-icon"><LifeBuoy size={18}/></div>
          <strong>Agent copilot</strong><p>Review policy-backed answers before taking any action.</p>
          <Link href="/operations">Open operations <ArrowUpRight size={14}/></Link>
        </div>
        <div className="p6-sidebar-user"><span className="p6-user-avatar">A</span><span><strong>Workspace agent</strong><small>Authenticated access</small></span><span className="p6-user-online"/></div>
      </div>
    </aside>
    <main className="p6-main">
      <div className="p6-topbar"><div className="p6-breadcrumb">Workspace <span>/</span> <strong>{title}</strong></div>
        <div className="p6-top-actions"><span className="p6-top-status"><span/>System ready</span><Link href="/operations" aria-label="Open approval queue" className="p6-icon-link"><ClipboardCheck size={18}/></Link></div>
      </div>
      <div className="p6-page-heading"><div><p className="p6-eyebrow">{eyebrow}</p><h1>{title}</h1><p className="p6-subtitle">{description}</p></div>{actions&&<div className="p6-heading-actions">{actions}</div>}</div>
      {demo&&<div className="p6-demo-notice"><strong>PREVIEW MODE</strong> — Illustrative sample records. No Supabase connection, real customer data, or live automation.</div>}
      <div className="p6-content">{children}</div>
      <footer className="p6-footer"><span>© ResolveOps · Agent-assisted support workspace</span><span>Internal drafts only · No live refunds or outbound emails</span></footer>
    </main>
  </div>
}

import Link from "next/link";
export default function DemoTabs(){
  return <div className="p6-demo-tabs" aria-label="Preview sections">
    <Link href="/showcase">Overview preview</Link>
    <Link href="/showcase/tickets">Tickets preview</Link>
    <Link href="/showcase/insights">Analytics preview</Link>
  </div>;
}

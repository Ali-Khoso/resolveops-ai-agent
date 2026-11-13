import type {Ticket,Customer} from "@/lib/workspace-api";

export type TicketFilter={query:string;status:string;priority:string;sort:"newest"|"oldest"|"priority"};
const priorityWeight:Record<string,number>={urgent:4,high:3,normal:2,low:1};

export function filterTickets(tickets:Ticket[],customers:Customer[],filter:TicketFilter):Ticket[]{
  const names=new Map(customers.map(c=>[c.id,c.full_name.toLowerCase()]));
  const q=filter.query.trim().toLowerCase();
  return tickets.filter(t=>
    (filter.status==="all"||t.status===filter.status)&&
    (filter.priority==="all"||t.priority===filter.priority)&&
    (!q||[t.subject,t.description,names.get(t.customer_id)||"",t.id].some(x=>x.toLowerCase().includes(q)))
  ).sort((a,b)=>{
    if(filter.sort==="priority")return (priorityWeight[b.priority]||0)-(priorityWeight[a.priority]||0)||b.created_at.localeCompare(a.created_at);
    return filter.sort==="oldest"?a.created_at.localeCompare(b.created_at):b.created_at.localeCompare(a.created_at);
  });
}

export function pageCount(length:number,pageSize:number):number{
  return Math.max(1,Math.ceil(Math.max(0,length)/pageSize));
}

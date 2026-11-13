import "../../phase6.css";
import Phase6Shell from "@/components/phase6/shell";
import TicketExplorer from "@/components/phase6/ticket-explorer";
import DemoTabs from "@/components/phase6/demo-tabs";
import {demoTickets,demoCustomers,demoOrders} from "@/lib/phase6-demo";
export const metadata={title:"Ticket preview — ResolveOps",robots:{index:false,follow:false}};
export default function ShowcaseTickets(){
 return <Phase6Shell active="/tickets" eyebrow="EXPLORE THE EXPERIENCE" title="Ticket explorer"
  description="Search, filter and inspect a synthetic queue with zero credentials." demo>
  <DemoTabs/><TicketExplorer tickets={demoTickets} customers={demoCustomers} orders={demoOrders}/>
 </Phase6Shell>;
}

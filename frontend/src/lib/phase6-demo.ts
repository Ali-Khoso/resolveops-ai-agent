/** Synthetic, deterministic sample records for PUBLIC showcase pages only.
 * Nothing in this module reads user data, keys, sessions or Supabase.
 */
import type {Ticket,Customer,Order} from "@/lib/workspace-api";
import type {Approval,Run,Analytics} from "@/lib/operations-api";
import type {OverviewData} from "@/components/phase6/overview";
const timestamp=(day:number)=>`2026-11-${String(day).padStart(2,"0")}T12:00:00.000Z`;
const ids=Array.from({length:12},(_,i)=>`demo-ticket-${String(i+1).padStart(2,"0")}`);
const customerNames=["Taylor Reed","Jordan Lee","Morgan Patel","Casey Blake","Sam Rivera","Avery Chen"];
export const demoCustomers:Customer[]=customerNames.map((name,i)=>({
  id:`demo-customer-${i+1}`,owner_id:"demo-only",full_name:name,
  email:`sample${i+1}@example.test`,phone:null,created_at:timestamp(4+i)
}));
export const demoOrders:Order[]=Array.from({length:8},(_,i)=>({
  id:`demo-order-${i+1}`,owner_id:"demo-only",customer_id:demoCustomers[i%6].id,
  item:["Wireless headphones","Desk lamp","Travel backpack","Mechanical keyboard","Laptop stand","Monitor arm","Water bottle","USB-C hub"][i],
  status:i<2?"shipped":i<5?"processing":"delivered",
  tracking_number:i<3?`DEMO-TRK-${1200+i}`:null,created_at:timestamp(3+i)
}));
const subject=[
"Order #4821 — delivery delayed","Return request for headphones","Package marked delivered, not received",
"Warranty coverage question","Shipping address correction","Refund eligibility review",
"Damaged item replacement","Tracking link not updating","Cancel pending order",
"Priority customer escalation","Invoice request","Replacement order status"
];
const desc=[
"Customer reports no shipment update for five days.",
"Requesting a return after receiving the wrong color.",
"Package does not appear at delivery address.",
"Customer needs warranty policy clarification.",
"Update delivery address before item ships.",
"Customer asks whether a refund is permitted under company policy.",
"Item arrived with visible damage and needs replacement.",
"Tracking page hasn't updated since dispatch.",
"Order is processing and customer wants to cancel.",
"Please escalate unresolved support discussion.",
"Customer needs a copy of the invoice.",
"Customer asks when replacement ships."
];
const status=["open","in_progress","open","resolved","open","in_progress","resolved","closed","open","in_progress","resolved","open"];
const priority=["high","normal","urgent","low","normal","high","normal","low","normal","urgent","low","normal"];
export const demoTickets:Ticket[]=ids.map((id,i)=>({
  id,owner_id:"demo-only",customer_id:demoCustomers[i%6].id,
  order_id:i<8?demoOrders[i].id:null,subject:subject[i],description:desc[i],
  priority:priority[i],status:status[i],created_at:timestamp(12-i)
}));
export const demoApprovals:Approval[]=Array.from({length:6},(_,i)=>({
  id:`demo-approval-${i+1}`,ticket_id:ids[i],run_id:`demo-run-${i+1}`,
  action_type:i%3===0?"refund_review":i%3===1?"send_reply":"resolve_ticket",
  draft_reply:"Internal draft awaiting reviewer confirmation.",
  reason:["Refund eligibility must be verified","Policy evidence needs human review","Proposed ticket closure needs approval"][i%3],
  status:i<3?"pending":i===3?"rejected":"approved",
  created_at:timestamp(11-i)
}));
export const demoRuns:Run[]=Array.from({length:6},(_,i)=>({
  id:`demo-run-${i+1}`,ticket_id:ids[i],question:desc[i],
  intent:["refund","order","escalation","policy","order","refund"][i],
  response:"INTERNAL DRAFT — human review required before customer use.",
  duration_ms:800+i*243,status:i<3?"pending_approval":"completed",
  requires_approval:i<3,workflow_steps:["classified","looked_up_owned_ticket","drafted_internal_response"],
  review_flags:i<3?["human_review_required"]:[],sources:[],created_at:timestamp(11-i)
}));
export const demoAnalytics:Analytics={
  tickets:demoTickets.length,
  open_tickets:demoTickets.filter(t=>["open","in_progress"].includes(t.status)).length,
  resolved_tickets:demoTickets.filter(t=>["resolved","closed"].includes(t.status)).length,
  investigations:demoRuns.length,avg_run_ms:1216,pending_approvals:3,approved_actions:2,
  real_email_sent:0,refunds_issued:0,
  notice:"Illustrative sample data. No real payment or outbound email integrations."
};
export const demoOverview:OverviewData={tickets:demoTickets,approvals:demoApprovals,runs:demoRuns,stats:demoAnalytics};

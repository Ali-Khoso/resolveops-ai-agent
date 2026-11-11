import { workspaceRequest } from "@/lib/workspace-api";

export type Run = {
  id:string; ticket_id:string; question:string; intent:string; response:string;
  duration_ms:number; status:string; requires_approval:boolean;
  workflow_steps?:string[]; review_flags?:string[];
  sources:Array<{citation:string;title:string;excerpt:string}>;created_at:string
};
export type Approval = {id:string;ticket_id:string;run_id:string|null;
  action_type:"send_reply"|"resolve_ticket"|"refund_review";draft_reply:string;
  reason:string;status:"pending"|"approved"|"rejected";created_at:string};
export type Audit = {id:string;approval_id:string;action_type:string;decision:string;created_at:string};
export type Analytics = {tickets:number;investigations:number;pending_approvals:number;
  open_tickets:number;resolved_tickets:number;approved_actions:number;avg_run_ms:number;
  real_email_sent:number;refunds_issued:number;notice:string};

const p="/operations";
export const listRuns=()=>workspaceRequest<{items:Run[]}>(p+"/investigations");
export const investigate=(ticket_id:string,question:string)=>
  workspaceRequest<{run:Run;suggested_action:string|null;steps:string[]}>(p+"/investigations",{
    method:"POST",body:JSON.stringify({ticket_id,question})
  });
export const listApprovals=()=>workspaceRequest<{items:Approval[]}>(p+"/approvals");
export const createApproval=(data:{ticket_id:string;run_id?:string;action_type:Approval["action_type"];
  draft_reply:string;reason:string})=>workspaceRequest<Approval>(p+"/approvals",{
    method:"POST",body:JSON.stringify(data)
  });
export const decide=(id:string,decision:"approved"|"rejected")=>
  workspaceRequest<Approval>(p+"/approvals/"+id+"/decision",{method:"POST",body:JSON.stringify({decision})});
export const listAudit=()=>workspaceRequest<{items:Audit[]}>(p+"/audit");
export const getAnalytics=()=>workspaceRequest<Analytics>(p+"/analytics");

import { workspaceRequest } from "@/lib/workspace-api";

export type Run = {
  id:string; ticket_id:string; question:string; intent:string; response:string;
  duration_ms:number; status:string; requires_approval:boolean;
  workflow_steps?:string[]; review_flags?:string[];
  sources:Array<{citation:string;title:string;excerpt:string}>;created_at:string
};
export type ApprovalStatus = "pending"|"approved"|"rejected";
export type Approval = {id:string;ticket_id:string;run_id:string|null;
  action_type:"send_reply"|"resolve_ticket"|"refund_review";draft_reply:string;
  reason:string;status:ApprovalStatus;created_at:string;
  decided_by?:string|null;decided_at?:string|null;decision_note?:string|null};
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
export const listApprovals = (status:"all"|ApprovalStatus="all",limit=50,offset=0)=>{
  const qs=new URLSearchParams({limit:String(limit),offset:String(offset)});
  if(status!=="all") qs.set("status",status);
  return workspaceRequest<{items:Approval[];limit:number;offset:number}>(p+"/approvals?"+qs.toString());
};
export const getApproval=(id:string)=>workspaceRequest<Approval>(p+"/approvals/"+encodeURIComponent(id));
export const createApproval=(data:{ticket_id:string;run_id?:string;action_type:Approval["action_type"];
  draft_reply:string;reason:string})=>workspaceRequest<Approval>(p+"/approvals",{
    method:"POST",body:JSON.stringify(data)
  });
export const decide=(id:string,decision:"approved"|"rejected",note?:string)=>
  workspaceRequest<Approval>(p+"/approvals/"+encodeURIComponent(id)+"/decision",{
    method:"POST",body:JSON.stringify({decision,note:note?.trim()||null})
  });
export const listAudit=(approvalId?:string,limit=50,offset=0)=>{
  const qs=new URLSearchParams({limit:String(limit),offset:String(offset)});
  if(approvalId) qs.set("approval_id",approvalId);
  return workspaceRequest<{items:Audit[];limit:number;offset:number}>(p+"/audit?"+qs.toString());
};
export const getAnalytics=()=>workspaceRequest<Analytics>(p+"/analytics");

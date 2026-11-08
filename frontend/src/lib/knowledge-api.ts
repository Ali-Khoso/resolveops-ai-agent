import { workspaceRequest } from "@/lib/workspace-api";
export type PolicyDocument = {
  id: string; title: string; filename: string; content_type: string;
  status: "processing" | "ready" | "failed"; chunk_count: number;
  error_message: string | null; created_at: string;
};
export type PolicySource = {
  citation: string; document_id: string; title: string; filename: string;
  page_number: number | null; chunk_index: number; similarity: number; excerpt: string;
};
export type PolicyAnswer = { answer: string; sources: PolicySource[]; grounded: boolean };
export const listPolicyDocuments = () => workspaceRequest<{items: PolicyDocument[]}>("/knowledge/documents");
export const removePolicyDocument = (id: string) => workspaceRequest<void>(`/knowledge/documents/${id}`, {method:"DELETE"});
export function uploadPolicy(file: File, title: string) {
  const body = new FormData();
  body.append("file", file);
  body.append("title", title);
  return workspaceRequest<PolicyDocument>("/knowledge/documents", {method:"POST", body});
}
export const askPolicies = (question: string) => workspaceRequest<PolicyAnswer>("/knowledge/ask", {
  method:"POST", body:JSON.stringify({question, top_k:5}),
});

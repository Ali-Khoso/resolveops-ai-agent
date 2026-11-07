import { getSupabase } from "@/lib/supabase";

const ROOT = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export type Customer = { id: string; owner_id: string; full_name: string; email: string; phone: string | null; created_at: string };
export type Order = { id: string; owner_id: string; customer_id: string; item: string; status: string; tracking_number: string | null; created_at: string };
export type Ticket = { id: string; owner_id: string; customer_id: string; order_id: string | null; subject: string; description: string; priority: string; status: string; created_at: string };
export type TicketMessage = { id: string; ticket_id: string; content: string; sender_type: string; created_at: string };
export type Profile = { user: {id: string; email: string}; profile: {display_name: string; role: string} };

export async function workspaceRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const supabase = getSupabase();
  if (!supabase) throw new Error("Supabase is not configured. See frontend/.env.example");
  const { data, error: sessionError } = await supabase.auth.getSession();
  if (sessionError || !data.session?.access_token) throw new Error("Your session expired. Please sign in again.");
  const response = await fetch(`${ROOT}/api/v1/workspace${path}`, {
    ...init,
    cache: "no-store",
    headers: { ...(init.body ? {"Content-Type": "application/json"} : {}),
      Authorization: `Bearer ${data.session.access_token}`,
      ...(init.headers || {}) },
  });
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body && typeof body.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const listCustomers = () => workspaceRequest<{items: Customer[]}>("/customers");
export const listOrders = () => workspaceRequest<{items: Order[]}>("/orders");
export const listTickets = () => workspaceRequest<{items: Ticket[]}>("/tickets");
export const getProfile = () => workspaceRequest<Profile>("/me");
export const listMessages = (ticketId: string) => workspaceRequest<{items: TicketMessage[]}>(`/tickets/${ticketId}/messages`);
export const addMessage = (ticketId: string, content: string) => workspaceRequest<TicketMessage>(`/tickets/${ticketId}/messages`, {method:"POST", body:JSON.stringify({content})});
export const createCustomer = (input: {full_name: string; email: string; phone?: string}) => workspaceRequest<Customer>("/customers", {method:"POST", body:JSON.stringify(input)});
export const createOrder = (input: {customer_id:string; item:string}) => workspaceRequest<Order>("/orders", {method:"POST", body:JSON.stringify(input)});
export const createTicket = (input: {customer_id:string; order_id?:string; subject:string; description:string; priority:string}) => workspaceRequest<Ticket>("/tickets", {method:"POST", body:JSON.stringify(input)});
export const changeTicketStatus = (id:string, status:string) => workspaceRequest<Ticket>(`/tickets/${id}`, {method:"PATCH", body:JSON.stringify({status})});

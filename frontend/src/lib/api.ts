export type Order = {
  order_id: string;
  customer: string;
  item: string;
  status: string;
  carrier: string | null;
  estimated_delivery: string | null;
};
export type Health = { status: string; service: string; agent_mode: "demo" | "ai"; demo_data: boolean };
export type ChatResult = { answer: string; mode: "demo" | "ai" };
const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, cache: "no-store" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
export const fetchHealth = () => request<Health>("/health");
export const fetchOrders = () => request<{ orders: Order[]; demo_data: boolean }>("/api/v1/orders");
export const sendMessage = (message: string) => request<ChatResult>("/api/v1/agent/chat", {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message }),
});

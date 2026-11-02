import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResolveOps — AI Support Operations",
  description: "Phase 1 customer support agent and operations dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

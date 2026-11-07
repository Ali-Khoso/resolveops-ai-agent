"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { getSupabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login"|"signup">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const supabase = getSupabase();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) { setNotice("Please configure Supabase in frontend/.env.local first."); return; }
    setBusy(true); setNotice("");
    try {
      if (mode === "signup") {
        const { data, error } = await supabase.auth.signUp({email, password, options: {data:{full_name:fullName}}});
        if (error) throw error;
        if (!data.session) { setNotice("Account requested. Check your email for the confirmation link, then sign in."); return; }
      } else {
        const { error } = await supabase.auth.signInWithPassword({email, password});
        if (error) throw error;
      }
      router.replace("/workspace");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Authentication failed"); }
    finally { setBusy(false); }
  }

  return <main className="auth-page">
    <div className="auth-card">
      <div className="auth-brand"><span className="brandmark"><Sparkles size={18}/></span><b>ResolveOps</b></div>
      <div className="eyebrow">SECURE WORKSPACE · PHASE 2</div>
      <h1>{mode === "login" ? "Welcome back" : "Create your workspace"}</h1>
      <p className="muted">{mode === "login" ? "Sign in to manage your own customers and support tickets." : "Each user gets a private support workspace protected by database policies."}</p>
      <form className="stackform" onSubmit={submit}>
        {mode === "signup" && <label>Full name<input aria-label="Full name" value={fullName} onChange={e=>setFullName(e.target.value)} minLength={2} maxLength={120} required placeholder="Support Agent"/></label>}
        <label>Email<input type="email" aria-label="Email" value={email} onChange={e=>setEmail(e.target.value)} required autoComplete="email" placeholder="you@company.com"/></label>
        <label>Password<input type="password" aria-label="Password" value={password} onChange={e=>setPassword(e.target.value)} minLength={6} required autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder="••••••••"/></label>
        <button type="submit" className="primarybtn big" disabled={busy || !supabase}>{busy ? "Working..." : mode === "login" ? "Sign in" : "Sign up"}<ArrowRight size={16}/></button>
      </form>
      {!supabase && <p className="notice">Supabase is not configured. Add the two NEXT_PUBLIC_SUPABASE variables and restart Next.js.</p>}
      {notice && <p className="notice" role="status">{notice}</p>}
      <div className="switchauth">{mode === "login" ? "New here? " : "Already registered? "}<button type="button" onClick={()=>{setMode(mode === "login" ? "signup" : "login");setNotice("");}}>{mode === "login" ? "Create an account" : "Sign in"}</button></div>
      <div className="auth-footer"><ShieldCheck size={15}/> Credentials are handled by Supabase Auth, not the ResolveOps API. <Link href="/">Back to demo</Link></div>
    </div>
  </main>;
}

import Link from "next/link";
export default function SettingsPage(){return <main style={{margin:"70px auto",maxWidth:800,padding:24,lineHeight:1.7}}>
  <h1>ResolveOps Settings</h1>
  <p>Configure Supabase and Gemini in local environment files, not the browser.</p>
  <p>Read <code>docs/PHASE4_7_SETUP.md</code> and run all three Supabase SQL migrations in order.</p>
  <p>No service-role key belongs in the frontend. No real payment or email API is integrated.</p>
  <Link href="/operations">Return to operations</Link>
</main>}

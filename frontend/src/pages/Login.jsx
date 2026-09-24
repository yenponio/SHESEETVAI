import { useRef,useState } from "react";
import { Link,useNavigate } from "react-router-dom";
import { ErrorState,Icon } from "../components/UI";
export default function Login() {
  const navigate = useNavigate(); const [email,setEmail] = useState(""); const [password,setPassword] = useState(""); const [busy,setBusy] = useState(false); const [error,setError] = useState(""); const pending = useRef(false);
  async function handleLogin(event) {
    event.preventDefault(); if (pending.current) return; pending.current = true;setBusy(true);setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/students/login/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
      const data = await response.json(); if (!response.ok || !data.success) throw new Error(data.message || "Sign-in failed.");
      localStorage.setItem("osaLoggedIn","true");localStorage.setItem("osaEmail",email);navigate("/dashboard");
    } catch (issue) { setError(issue.message || "Cannot connect to the server."); }
    finally { pending.current = false;setBusy(false); }
  }
  return <main className="login-page container-fluid"><div className="login-card card"><div className="card-body p-4 p-sm-5"><div className="brand-panel mb-4"><Icon name="shield-check" className="fs-2" /><div><strong>SHESEETVAI</strong><small>Campus dress-code review</small></div></div><h1>Welcome, OSA</h1><p className="text-muted small mb-4">Sign in to review inspections and campus records.</p><ErrorState error={error} />
    <form onSubmit={handleLogin}><div className="mb-3"><label htmlFor="osa-email" className="form-label">Email address</label><input id="osa-email" name="email" className="form-control" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)} /></div><div className="mb-4"><label htmlFor="osa-password" className="form-label">Password</label><input id="osa-password" name="password" className="form-control" type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)} /></div><button type="submit" className="btn btn-primary w-100" disabled={busy}>{busy ? "Signing in..." : "Sign in"}<Icon name="arrow-right" /></button></form><Link to="/" className="btn btn-link w-100 mt-3">Return to student scanner</Link></div></div></main>;
}

import { Link, useNavigate } from "react-router-dom";
export default function Topbar({ title, compact, toggleDesktop, openMobile }) {
  const navigate = useNavigate();
  function logout() { localStorage.removeItem("osaLoggedIn"); localStorage.removeItem("osaEmail"); navigate("/osa"); }
  return <header className="topbar navbar">
    <div className="d-flex align-items-center gap-3 min-w-0">
      <button className="btn btn-icon d-lg-none" onClick={openMobile} aria-label="Open navigation" aria-haspopup="dialog"><i className="bi bi-list" aria-hidden="true" /></button>
      <button className="btn btn-icon d-none d-lg-inline-flex" onClick={toggleDesktop} aria-label={compact ? "Expand navigation" : "Collapse navigation"} aria-controls="desktop-navigation" aria-expanded={!compact}><i className="bi bi-layout-sidebar" aria-hidden="true" /></button>
      <div><span className="eyebrow d-none d-sm-block">OFFICE OF STUDENT AFFAIRS</span><span className="topbar-title">{title}</span></div>
    </div>
    <div className="d-flex align-items-center gap-2">
      <Link to="/email-notifications" className="btn btn-icon" aria-label="Email notifications"><i className="bi bi-bell" aria-hidden="true" /></Link>
      <details className="account-menu"><summary className="btn btn-account"><span className="avatar">OSA</span><span className="d-none d-md-inline">OSA account</span><i className="bi bi-chevron-down" aria-hidden="true" /></summary>
        <div className="account-dropdown"><p className="small text-muted mb-2">{localStorage.getItem("osaEmail") || "OSA workspace"}</p>
          <Link to="/settings" className="dropdown-item">System settings</Link><button className="dropdown-item" onClick={logout}>Logout</button></div>
      </details>
    </div>
  </header>;
}

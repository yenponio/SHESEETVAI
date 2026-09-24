import { NavLink, useNavigate } from "react-router-dom";
import { navigation } from "../navigation";
export default function Sidebar({ compact = false, onNavigate = () => {} }) {
  const navigate = useNavigate();
  function logout() { localStorage.removeItem("osaLoggedIn"); localStorage.removeItem("osaEmail"); onNavigate(); navigate("/osa"); }
  return <div className={`sidebar-inner ${compact ? "sidebar-compact" : ""}`}>
    <div className="brand-panel"><span className="brand-mark"><i className="bi bi-shield-check" aria-hidden="true" /></span>
      <div className="nav-label"><strong>SHESEETVAI</strong><small>Campus dress-code review</small></div></div>
    <div className="nav-caption nav-label">OSA WORKSPACE</div>
    <nav aria-label="Main navigation" className="nav flex-column gap-1">
      {navigation.map(([to, icon, label]) => <NavLink key={to} to={to} title={compact ? label : undefined}
        className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} onClick={onNavigate}>
        <i className={`bi bi-${icon}`} aria-hidden="true" /><span className="nav-label">{label}</span><span className="visually-hidden">{compact ? label : ""}</span>
      </NavLink>)}
    </nav>
    <div className="sidebar-bottom"><NavLink className="nav-link" to="/" onClick={onNavigate} title="Student scanner">
      <i className="bi bi-upc-scan" aria-hidden="true" /><span className="nav-label">Student scanner</span><span className="visually-hidden">{compact ? "Student scanner" : ""}</span></NavLink>
      <button className="nav-link w-100" onClick={logout} title="Logout"><i className="bi bi-box-arrow-right" aria-hidden="true" /><span className="nav-label">Logout</span><span className="visually-hidden">{compact ? "Logout" : ""}</span></button></div>
  </div>;
}

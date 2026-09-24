import { Icon } from "../UI";
export default function StatCard({ title, value, icon, help }) {
  return <div className="card h-100"><div className="card-body stat-card"><span className="stat-icon"><Icon name={icon} /></span><div><p className="stat-label">{title}</p><div className="stat-value">{value ?? "Unavailable"}</div>{help && <p className="stat-help">{help}</p>}</div></div></div>;
}

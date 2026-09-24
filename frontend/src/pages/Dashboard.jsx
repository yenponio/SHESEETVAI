import { Link } from "react-router-dom";
import useLiveData from "../hooks/useLiveData";
import StatCard from "../components/dashboard/StatCard";
import CollegeChart from "../components/dashboard/CollegeChart";
import ComplianceChart from "../components/dashboard/ComplianceChart";
import { PageHeading, StatusBadge, EmptyState, LoadingState, ErrorState, Icon } from "../components/UI";
import { gateMessage } from "../hooks/useGateCycle";
const API = "http://127.0.0.1:8000/api/students/";
export default function Dashboard() {
  const { data, error } = useLiveData(`${API}dashboard/`);
  const system = useLiveData(`${API}system-status/`);
  const camera = useLiveData("http://127.0.0.1:5000/camera-status");
  const unavailable = system.error ? "Unavailable" : "Loading...";
  return <><PageHeading title="Campus overview" description="A clear view of today's activity and official dress-code records."><Link className="btn btn-primary" to="/chatbot"><Icon name="camera-video" />Open live review</Link></PageHeading>
    <ErrorState error={error || system.error} />
    <div className="row g-3 mb-4">
      <div className="col-6 col-xl-3"><StatCard title="ID scans today" value={system.data?.scans_today ?? unavailable} icon="upc-scan" help="All recorded scan attempts" /></div>
      <div className="col-6 col-xl-3"><StatCard title="Official offenses today" value={data?.violations_today ?? (error ? "Unavailable" : "Loading...")} icon="journal-check" help="Confirmed and entered" /></div>
      <div className="col-6 col-xl-3"><StatCard title="Confirmed entries today" value={system.data?.entries_today ?? unavailable} icon="door-open" help="Sensor-confirmed passage" /></div>
      <div className="col-6 col-xl-3"><StatCard title="Denied attempts today" value={system.data?.denied_today ?? unavailable} icon="shield-x" help="Excluded from offenses" /></div>
    </div>
    <div className="row g-4 mb-4"><div className="col-lg-7"><div className="card h-100"><div className="card-body">{data ? <CollegeChart data={data.college_chart} /> : error ? <EmptyState title="Statistics unavailable" /> : <LoadingState />}</div></div></div>
      <div className="col-lg-5"><div className="card h-100"><div className="card-body">{data ? <ComplianceChart data={data.compliance_chart} /> : error ? <EmptyState title="Summary unavailable" /> : <LoadingState />}</div></div></div></div>
    <div className="row g-4 mb-4"><div className="col-xl-8"><section className="card h-100"><div className="card-body"><div className="d-flex justify-content-between align-items-center gap-3 mb-3"><h2 className="mb-0">Recent campus entries</h2><Link to="/scan-history" className="btn btn-outline-primary btn-sm">View logs</Link></div>
      <div className="table-responsive"><table className="table"><thead><tr><th>Student</th><th>School</th><th>Official history</th><th>Entry time</th></tr></thead><tbody>{data?.recent_logs.map((item, index) => <tr key={`${item.studentNumber}-${item.time}-${index}`}><td><strong>{item.name}</strong><div className="small text-muted">{item.studentNumber}</div></td><td>{item.college}</td><td><StatusBadge icon="journal">{item.status}</StatusBadge></td><td className="text-nowrap">{new Date(item.time).toLocaleTimeString("en-PH", { timeZone:"Asia/Manila", hour:"2-digit", minute:"2-digit" })}</td></tr>)}</tbody></table></div>
      {data && !data.recent_logs.length && <EmptyState title="No campus entries yet" />}{!data && !error && <LoadingState />}</div></section></div>
      <div className="col-xl-4"><section className="card h-100"><div className="card-body"><h2 className="mb-3">System connections</h2><div className="d-grid gap-3">
        <div className="summary-line"><span>Arduino Uno</span><StatusBadge icon="usb-symbol">{system.error ? "Unavailable" : system.data ? system.data.arduino_connected ? "Connected" : "Offline" : "Checking..."}</StatusBadge></div>
        <div className="summary-line"><span>Camera service</span><StatusBadge icon="camera-video">{camera.error ? "Unavailable" : camera.data ? camera.data.active ? "Streaming" : "Idle" : "Checking..."}</StatusBadge></div>
        <div className="summary-line"><span>SMTP configuration</span><StatusBadge icon="envelope">{system.data ? system.data.smtp_configured ? "Configured" : "Not configured" : unavailable}</StatusBadge></div></div>
        <p className="small text-muted mt-3 mb-0">{system.data?.active_cycle ? gateMessage(system.data.active_cycle) : "No active gate attempt reported."}</p><Link to="/settings" className="btn btn-link mt-2">Connection details</Link></div></section></div></div>
    <section className="card"><div className="card-body"><h2>Recent AI inspections</h2><p className="small text-muted">Review activity only. These are not automatically official offenses.</p>
      <div className="table-responsive"><table className="table"><thead><tr><th>Student</th><th>AI result</th><th>OSA decision</th><th>Captured (Manila)</th></tr></thead><tbody>{system.data?.recent_detections.map(item => <tr key={item.id}><td>{item.name}<div className="small text-muted">{item.student_number}</div></td><td><StatusBadge icon="camera">{item.ai_result}</StatusBadge></td><td>{item.decision.replaceAll("_", " ")}</td><td>{new Date(item.detected_at).toLocaleString("en-PH", {timeZone:"Asia/Manila"})}</td></tr>)}</tbody></table></div>{system.data && !system.data.recent_detections.length && <EmptyState title="No inspections yet" />}</div></section>
  </>;
}

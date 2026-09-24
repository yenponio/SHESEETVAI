import { StatusBadge } from "../UI";
export default function ComplianceChart({ data = [] }) {
  return <><h2>Student offense summary</h2><p className="small text-muted">Each registered student is counted once, using official history.</p>
    <div className="d-grid gap-3">{data.map((item, index) => <div className="summary-line" key={item.name}><StatusBadge icon={index ? "journal-check" : "shield-check"}>{item.name}</StatusBadge><strong className="fs-4">{item.value}</strong></div>)}</div>
    <p className="small text-muted mt-4 mb-0">Every 3 total minor offenses equals 1 major equivalent. The full minor history is retained.</p></>;
}

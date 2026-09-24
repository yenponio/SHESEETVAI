import { EmptyState } from "../UI";
export default function CollegeChart({ data = [] }) {
  const largest = Math.max(1, ...data.map(item => item.violations));
  return <><h2>Official offenses by school</h2><p className="small text-muted">All recorded official offenses</p>
    {data.length ? <ul className="school-chart list-unstyled mb-0">{data.map(item => <li key={item.college}><span>{item.college}</span><div className="chart-track"><div className="chart-fill" style={{ width: `${item.violations / largest * 100}%` }} /></div><strong>{item.violations}</strong></li>)}</ul> : <EmptyState title="No official offenses" />}</>;
}

import { useId, useState } from "react";
import ViolationEvidenceModal from "./ViolationEvidenceModal";
import { SearchBar, Pagination, EmptyState, LoadingState, ErrorState, StatusBadge, Icon } from "./UI";
export default function ViolationTable({ records, loading, error }) {
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [search, setSearch] = useState("");
  const [date, setDate] = useState("");
  const [type, setType] = useState("");
  const [decision, setDecision] = useState("");
  const [page, setPage] = useState(1);
  const id = useId();
  const filtered = records.filter(item => [item.studentNumber,item.name,item.college].some(value => String(value || "").toLowerCase().includes(search.toLowerCase())) && (!date || item.date === date) && (!type || item.violationType === type) && (!decision || item.osa_decision === decision));
  const pages = Math.max(1,Math.ceil(filtered.length/10));
  const current = Math.min(page,pages);
  function change(setter,value) { setter(value);setPage(1); }
  return <><ErrorState error={error} /><div className="row g-3 my-2"><div className="col-md-6 col-xl-4"><SearchBar label="Search official records" placeholder="Student name, ID or school" value={search} onChange={value => change(setSearch,value)} /></div>
    <div className="col-6 col-md-3 col-xl-2"><label className="form-label" htmlFor={`${id}-date`}>Date (Manila)</label><input type="date" className="form-control" id={`${id}-date`} value={date} onChange={event => change(setDate,event.target.value)} /></div>
    <div className="col-6 col-md-3 col-xl-3"><label className="form-label" htmlFor={`${id}-type`}>Violation</label><select className="form-select" id={`${id}-type`} value={type} onChange={event => change(setType,event.target.value)}><option value="">All types</option>{[...new Set(records.map(item => item.violationType))].filter(Boolean).sort().map(value => <option key={value}>{value}</option>)}</select></div>
    <div className="col-md-6 col-xl-3"><label className="form-label" htmlFor={`${id}-decision`}>OSA decision</label><select className="form-select" id={`${id}-decision`} value={decision} onChange={event => change(setDecision,event.target.value)}><option value="">All recorded decisions</option>{[...new Set(records.map(item => item.osa_decision))].filter(Boolean).map(value => <option key={value} value={value}>{value.replaceAll("_"," ")}</option>)}</select></div></div>
    <p className="small text-muted mt-3">Only official confirmed-entry offenses are listed. Counts show the student's current totals.</p>
    {loading ? <LoadingState /> : <><div className="table-responsive"><table className="table"><thead><tr><th>Student</th><th>Evidence</th><th>Violation</th><th>Entry / Decision</th><th>Minor / Major eq.</th><th>Email</th><th>Date / Time</th><th>Details</th></tr></thead><tbody>{filtered.slice((current-1)*10,current*10).map(record => <tr key={record.id}>
      <td><button className="btn btn-link" onClick={() => setSelectedRecord(record)}>{record.name}</button><div className="small text-muted">{record.studentNumber}</div></td>
      <td>{record.evidence_image ? <button className="evidence-thumb" aria-label={`View evidence for ${record.name}`} onClick={() => setSelectedRecord(record)}><img src={record.evidence_image} alt="Recorded evidence thumbnail" onError={event => { event.currentTarget.style.visibility = "hidden"; }} /><Icon name="image" /></button> : <span className="small text-muted">No image</span>}</td>
      <td>{record.violationType || "Unspecified"}</td><td><StatusBadge icon="door-open">{record.confirmed_entry ? "Entry confirmed" : "Not reported"}</StatusBadge><div className="small text-muted mt-1">{record.osa_decision?.replaceAll("_"," ") || "Legacy record"}</div></td>
      <td className="text-nowrap">{record.total_minor_offenses ?? "?"} / {record.equivalent_major_offenses ?? "?"}</td><td>{record.email_status || "No delivery record"}</td><td className="text-nowrap">{record.date}<div className="small text-muted">{record.time} Manila</div></td><td><button className="btn btn-outline-primary btn-sm" aria-label={`View details for ${record.name} on ${record.date}`} onClick={() => setSelectedRecord(record)}>View</button></td></tr>)}</tbody></table></div>
      {!filtered.length && <EmptyState title={error ? "Records unavailable" : "No official records match"} message="Try clearing your search or filters." />}<Pagination total={filtered.length} page={current} pages={pages} onChange={setPage} /></>}
    {selectedRecord && <ViolationEvidenceModal record={selectedRecord} onClose={() => setSelectedRecord(null)} />}</>;
}

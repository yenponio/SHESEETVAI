import { useState } from "react";
import { Link } from "react-router-dom";
import useLiveData from "../hooks/useLiveData";
import { PageHeading, SearchBar, Pagination, LoadingState, EmptyState, ErrorState, Icon } from "../components/UI";
export default function Students() {
  const { data, error } = useLiveData("http://127.0.0.1:8000/api/students/");
  const [search, setSearch] = useState("");
  const [school, setSchool] = useState("");
  const [offenses, setOffenses] = useState("");
  const [page, setPage] = useState(1);
  const students = Array.isArray(data) ? data : [];
  const filtered = students.filter(item => [item.student_number,item.full_name,item.email,item.barcode].some(value => String(value || "").toLowerCase().includes(search.toLowerCase())) && (!school || item.college === school) && (!offenses || (offenses === "recorded" ? item.offense_counts.total_minor_offenses > 0 : item.offense_counts.total_minor_offenses === 0)));
  const pages = Math.max(1,Math.ceil(filtered.length / 10));
  const current = Math.min(page,pages);
  return <><PageHeading title="Students" description="Registered student identities and backend-derived official offense totals."><span className="status-badge"><Icon name="people" />{data ? `${students.length} registered` : "Loading roster"}</span></PageHeading>
    <ErrorState error={error} /><section className="card"><div className="card-body"><div className="row g-3 mb-4"><div className="col-md-6"><SearchBar label="Search students" placeholder="Name, student ID, barcode or email" value={search} onChange={value => {setSearch(value);setPage(1);}} /></div>
    <div className="col-sm-6 col-md-3"><label className="form-label" htmlFor="student-school-filter">School</label><select id="student-school-filter" className="form-select" value={school} onChange={event => {setSchool(event.target.value);setPage(1);}}><option value="">All schools</option>{[...new Set(students.map(item => item.college))].sort().map(value => <option key={value}>{value}</option>)}</select></div>
    <div className="col-sm-6 col-md-3"><label className="form-label" htmlFor="student-offense-filter">Official history</label><select id="student-offense-filter" className="form-select" value={offenses} onChange={event => {setOffenses(event.target.value);setPage(1);}}><option value="">All students</option><option value="recorded">With official offenses</option><option value="none">No official offenses</option></select></div></div>
    {!data && !error ? <LoadingState /> : <><div className="table-responsive"><table className="table"><thead><tr><th>Student ID / Barcode</th><th>Name / School</th><th>Email</th><th>Minor offenses</th><th>Major equivalent</th><th>Actions</th></tr></thead><tbody>{filtered.slice((current-1)*10,current*10).map(item => <tr key={item.id}><td className="text-nowrap"><strong>{item.student_number}</strong><div className="small text-muted">{item.barcode || "No barcode"}</div></td><td><strong>{item.full_name}</strong><div className="small text-muted">{item.college}</div></td><td>{item.email || "No email recorded"}</td><td>{item.offense_counts?.total_minor_offenses ?? "Not available"}</td><td>{item.offense_counts?.equivalent_major_offenses ?? "Not available"}</td><td><Link className="btn btn-outline-primary btn-sm text-nowrap" to={`/students/${encodeURIComponent(item.student_number)}`} aria-label={`View profile of ${item.full_name}`}><Icon name="person-vcard" />View profile</Link></td></tr>)}</tbody></table></div>{!filtered.length && <EmptyState title={error ? "Student data unavailable" : "No students match"} message="Try a different search or school filter." />}<Pagination page={current} pages={pages} total={filtered.length} onChange={setPage} /></>}
    </div></section><p className="small text-muted mt-3">Student creation and editing are not exposed by the current student API. This roster is read-only.</p></>;
}

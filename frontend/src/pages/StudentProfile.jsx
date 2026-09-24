import { Link, useParams } from "react-router-dom";
import useLiveData from "../hooks/useLiveData";
import ViolationTable from "../components/ViolationTable";
import EvidenceImage from "../components/EvidenceImage";
import { PageHeading, Detail, ErrorState, EmptyState, LoadingState, Icon } from "../components/UI";
const API = "http://127.0.0.1:8000/api/students/";
export default function StudentProfile() {
  const { studentNumber } = useParams();
  const roster = useLiveData(API);
  const records = useLiveData(`${API}records/`);
  const entries = useLiveData(`${API}audit/?student_number=${encodeURIComponent(studentNumber)}`);
  const student = roster.data?.find(item => item.student_number === studentNumber);
  const history = records.data?.records.filter(item => item.studentNumber === studentNumber) || [];
  return <><PageHeading title={student?.full_name || "Student profile"} description="Identity, campus activity and official offense history."><Link to="/students" className="btn btn-outline-primary"><Icon name="arrow-left" />Students</Link></PageHeading><ErrorState error={roster.error || records.error || entries.error} />
    {!roster.data && !roster.error ? <LoadingState /> : !student ? <EmptyState title="Student not found" /> : <><div className="row g-4 mb-4"><div className="col-lg-7"><div className="card h-100"><div className="card-body"><h2>Identity & contact information</h2><div className="student-review-heading mt-3">{student.id_front && <img src={student.id_front} alt={`ID of ${student.full_name}`} />}<div><h3>{student.full_name}</h3><span className="text-muted small">{student.student_number}</span></div></div><dl className="detail-list"><Detail label="Student ID">{student.student_number}</Detail><Detail label="Barcode">{student.barcode || "Not recorded"}</Detail><Detail label="School">{student.college}</Detail><Detail label="Email">{student.email || "Not recorded"}</Detail></dl></div></div></div>
      <div className="col-lg-5"><div className="card h-100"><div className="card-body"><h2>Offense & entry summary</h2><dl className="detail-list mt-4"><Detail label="Current minor offenses">{student.offense_counts?.total_minor_offenses}</Detail><Detail label="Equivalent major offenses">{student.offense_counts?.equivalent_major_offenses}</Detail><Detail label="Recorded scans">{entries.data?.total}</Detail><Detail label="Sensor-confirmed entries">{entries.data?.entered_total}</Detail></dl><p className="small text-muted mt-3 mb-0">Minor history is retained. Denied entry and rejected detections do not add official offenses.</p></div></div></div></div>
      <div className="row g-4 mb-4"><div className="col-lg-5"><section className="card h-100"><div className="card-body"><h2>Most recent official evidence</h2><EvidenceImage src={history[0]?.evidence_image} alt={`Evidence for ${student.full_name}'s most recent official report`} /><p className="small text-muted mt-2 mb-0">{history[0] ? `${history[0].date} ? ${history[0].violationType}` : "No official evidence report."}</p></div></section></div>
      <div className="col-lg-7"><section className="card h-100"><div className="card-body"><h2>Recent entry activity</h2><div className="table-responsive"><table className="table"><thead><tr><th>Scan (Manila)</th><th>OSA decision</th><th>Entry outcome</th></tr></thead><tbody>{entries.data?.results.slice(0,5).map(item => <tr key={item.id}><td>{new Date(item.scan_time).toLocaleString("en-PH",{timeZone:"Asia/Manila"})}</td><td>{item.osa_decision?.replaceAll("_"," ") || "Not reviewed"}</td><td>{item.outcome?.replaceAll("_"," ") || "Not recorded"}</td></tr>)}</tbody></table></div>{entries.data && !entries.data.results.length && <EmptyState title="No entry activity" />}</div></section></div></div>
      <section className="card"><div className="card-body"><h2>Official violation history</h2><ViolationTable records={history} loading={!records.data && !records.error} error={records.error} /></div></section></>}
  </>;
}

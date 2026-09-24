import Modal from "./Modal";
import EvidenceImage from "./EvidenceImage";
import { Detail, StatusBadge } from "./UI";
export default function ViolationEvidenceModal({ record, onClose }) {
  return <Modal large title="Official violation evidence" onClose={onClose} footer={<button className="btn btn-outline-primary" onClick={onClose}>Close details</button>}>
    <dl className="detail-list mb-4"><Detail label="Student">{record.name}</Detail><Detail label="Student ID">{record.studentNumber}</Detail><Detail label="College / school">{record.collegeName || record.college}</Detail><Detail label="Violation">{record.violationType || "Unspecified"}</Detail><Detail label="Recorded (Manila)">{record.date} | {record.time}</Detail><Detail label="OSA decision">{record.osa_decision?.replaceAll("_"," ") || "Not recorded in legacy history"}</Detail><Detail label="Current minor offenses">{record.total_minor_offenses}</Detail><Detail label="Equivalent major offenses">{record.equivalent_major_offenses}</Detail></dl>
    <div className="d-flex flex-wrap gap-2 mb-3">{record.confirmed_entry && <StatusBadge icon="door-open">Sensor-confirmed entry</StatusBadge>}<StatusBadge icon="envelope">Email: {record.email_status || "No delivery record"}</StatusBadge></div>
    <EvidenceImage src={record.evidence_image} alt={`Recorded violation evidence for ${record.name} on ${record.date} at ${record.time}`} />
  </Modal>;
}

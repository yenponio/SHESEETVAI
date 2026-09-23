import { useState } from "react";
import ViolationEvidenceModal from "./ViolationEvidenceModal";

export default function ViolationTable({ records, loading, error }) {
  const [selectedRecord, setSelectedRecord] = useState(null);
  return (
    <>
    <table>
      <thead>
        <tr>
          <th>Student No.</th><th>Name</th><th>School</th>
          <th>Violation Type</th><th>Date</th><th>Time (Manila)</th>
        </tr>
      </thead>
      <tbody>
        {records.map(record => (
          <tr key={record.id}>
            <td>{record.studentNumber}</td>
            <td><button type="button" className="student-link"
              onClick={() => setSelectedRecord(record)}
              aria-label={`View violation evidence for ${record.name} on ${record.date} at ${record.time}`}>
              {record.name}
            </button></td>
            <td title={record.collegeName}>{record.college}</td>
            <td>{record.violationType || "Unspecified"}</td>
            <td>{record.date}</td><td>{record.time}</td>
          </tr>
        ))}
        {records.length === 0 && (
          <tr><td colSpan="6">
            {loading ? "Loading violation records..." : error ? "Violation records are unavailable." : "No violation records found."}
          </td></tr>
        )}
      </tbody>
    </table>
    {selectedRecord && <ViolationEvidenceModal key={selectedRecord.id}
      record={selectedRecord} onClose={() => setSelectedRecord(null)} />}
    </>
  );
}

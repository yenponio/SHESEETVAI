import { useEffect, useRef, useState } from "react";

export default function ViolationEvidenceModal({ record, onClose }) {
  const dialogRef = useRef(null);
  const [imageFailed, setImageFailed] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    const opener = document.activeElement;
    dialog.showModal();
    return () => {
      dialog.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, []);

  return (
    <dialog ref={dialogRef} className="evidence-modal" aria-labelledby="evidence-title"
      onCancel={event => { event.preventDefault(); onClose(); }}>
      <div className="evidence-header">
        <h2 id="evidence-title">Violation Evidence</h2>
        <button type="button" className="view-btn" onClick={onClose} autoFocus>Close</button>
      </div>
      <dl className="evidence-details">
        <dt>Student</dt><dd>{record.name}</dd>
        <dt>Student Number</dt><dd>{record.studentNumber}</dd>
        <dt>School</dt><dd>{record.collegeName || record.college}</dd>
        <dt>Violation</dt><dd>{record.violationType || "Unspecified"}</dd>
        <dt>Date/Time (Manila)</dt><dd>{record.date} {record.time}</dd>
      </dl>
      {record.evidence_image && !imageFailed ? (
        <img className="evidence-image" src={record.evidence_image}
          alt={`Violation evidence for ${record.name} on ${record.date} at ${record.time}`}
          onError={() => setImageFailed(true)} />
      ) : <p role="status">No evidence image available.</p>}
    </dialog>
  );
}

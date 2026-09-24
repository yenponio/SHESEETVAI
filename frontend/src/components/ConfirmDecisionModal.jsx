import Modal from "./Modal";
import { ErrorState, Icon } from "./UI";
const descriptions = {
  YES: ["Confirm violation and allow entry", "Confirm this violation and allow the student to enter?", "An official offense can be recorded only after sensor-confirmed entry and the backend daily check."],
  NO: ["No violation", "Mark this AI result as no violation and allow entry?", "Normal entry may be logged. No offense or violation email will be created."],
  DENY: ["Confirm violation and deny entry", "Confirm this violation and deny campus entry?", "The gate remains closed. No official offense is created and no offense email is sent."],
};
export default function ConfirmDecisionModal({ selection, busy, error, onClose, onSubmit }) {
  const [title, question, detail] = descriptions[selection.decision];
  return <Modal id="confirmation-modal" title={title} busy={busy} onClose={onClose} footer={<>
    <button className="btn btn-outline-primary" disabled={busy} onClick={onClose}>Cancel</button>
    <button className="btn btn-primary" disabled={busy} onClick={onSubmit}>{busy ? <><span className="spinner-border spinner-border-sm" />Submitting...</> : <><Icon name="check2" />Submit decision</>}</button>
  </>}><p className="fw-semibold">{question}</p><p>{selection.inspection.student.name} | {selection.inspection.student.student_number}</p><div className="alert sh-alert mb-0"><Icon name={selection.decision === "DENY" ? "shield-x" : "info-circle"} /> {detail}</div><ErrorState error={error} /></Modal>;
}

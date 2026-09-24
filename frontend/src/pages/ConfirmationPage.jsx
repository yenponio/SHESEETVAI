import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import useLiveData from "../hooks/useLiveData";
import useGateCycle, { gateMessage } from "../hooks/useGateCycle";
import ConfirmDecisionModal from "../components/ConfirmDecisionModal";
import EvidenceImage from "../components/EvidenceImage";
import { PageHeading, StatusBadge, ErrorState, EmptyState, LoadingState, Detail, Icon } from "../components/UI";
const API = "http://127.0.0.1:8000/api/students/";
const OSA_DECISION_KEY = "sheseetv_osa_decision";
export default function ConfirmationPage() {
  const pending = useLiveData(`${API}ai-inspection/pending/`);
  const roster = useLiveData(API);
  const camera = useLiveData("http://127.0.0.1:5000/camera-status");
  const [selection, setSelection] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const inFlight = useRef(false);
  const candidate = pending.data?.success ? pending.data.inspection : null;
  const inspection = candidate?.id === result?.inspectionId ? null : candidate;
  const currentGate = useGateCycle(inspection?.attempt_id);
  const resultGate = useGateCycle(result?.attemptId);
  const student = roster.data?.find(item => item.student_number === inspection?.student.student_number);
  function choose(decision) { if (!processing && inspection) { setError(""); setSelection({ decision, inspection }); } }
  async function submit() {
    if (inFlight.current || !selection) return;
    inFlight.current = true;
    setProcessing(true);
    setError("");
    const { decision, inspection: review } = selection;
    try {
      const response = await fetch(`${API}ai-inspection/review/`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({inspection_id:review.id, decision}) });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.message || "Unable to submit this decision.");
      localStorage.setItem(OSA_DECISION_KEY, JSON.stringify({student_number:review.student.student_number, decision, inspection_id:review.id, attempt_id:review.attempt_id, timestamp:Date.now()}));
      setResult({ decision, inspectionId:review.id, attemptId:review.attempt_id, name:review.student.name, message:data.message });
      setSelection(null);
    } catch (issue) { setError(issue.message || "Cannot connect to the server. No opening has been confirmed."); }
    finally { inFlight.current = false; setProcessing(false); }
  }
  return <><PageHeading title="Live detection & review" description="Review the evidence. OSA authorizes entry; the sensor confirms passage."><Link className="btn btn-outline-primary" to="/"><Icon name="upc-scan" />Student scanner</Link></PageHeading>
    <ErrorState error={pending.error} />
    {result && <section className="alert sh-alert" role="status" id="review-result-toast"><div className="d-flex align-items-center gap-2 mb-1"><Icon name={result.decision === "DENY" ? "shield-x" : "check2-circle"} /><strong>{result.decision === "DENY" ? "ENTRY DENIED" : result.decision === "NO" ? "No violation confirmed" : "Confirm-and-allow decision submitted"}</strong></div><div className="small">{result.name} | {result.message}</div>
      <div className="small mt-1">{result.decision === "DENY" ? "Gate remains closed. No official offense recorded." : resultGate.error || (resultGate.cycle ? gateMessage(resultGate.cycle) : "Waiting for gate acknowledgement. Entry has not been confirmed.")}</div></section>}
    <div className="row g-4 align-items-start"><div className="col-lg-7 col-xl-8"><section className="card"><div className="card-body"><div className="d-flex justify-content-between align-items-center gap-2 mb-3"><h2 className="mb-0">Captured evidence</h2><StatusBadge icon="camera-video">{camera.error ? "Camera service unavailable" : camera.data ? camera.data.active ? "Camera active" : "Camera idle" : "Checking camera"}</StatusBadge></div>
      {inspection ? <EvidenceImage id="captured-student-image" src={inspection.screenshot} alt={`Inspection evidence for ${inspection.student.name}`} /> : <div className="media-frame">{!pending.data && !pending.error ? <LoadingState message="Checking the review queue..." /> : <EmptyState icon="camera" title="Ready for the next inspection" message="Scan a registered student ID at the scanner. Captured evidence will appear here when the AI submits its result." />}</div>}
      <div className="media-caption"><span><Icon name="image" /> {inspection ? `Inspection #${inspection.id}` : "Exact inspection evidence"}</span><span>{inspection ? new Date(inspection.detected_at).toLocaleString("en-PH", {timeZone:"Asia/Manila"}) + " (Manila)" : "No pending image"}</span></div>
      <div className="review-status-row"><div><span className="section-label">Scan / review</span><p className="mb-0 small">{inspection ? "AI complete - awaiting OSA decision" : "Waiting for inspection"}</p></div><div id="entrance-sensor-status"><span className="section-label">HC-SR04 passage</span><p className="mb-0 small">{currentGate.cycle ? currentGate.cycle.outcome.replaceAll("_", " ") : "No current passage reported"}</p></div></div>
    </div></section><p className="small text-muted mt-3"><Icon name="info-circle" /> Live camera processing stays on the student scanner. This page reviews its captured evidence.</p></div>
    <div className="col-lg-5 col-xl-4"><section className="card review-panel"><div className="card-body"><div className="d-flex justify-content-between gap-2 mb-3"><h2 className="mb-0">Student review</h2><StatusBadge icon="person-check">{inspection ? "Awaiting decision" : "No pending review"}</StatusBadge></div>
      {inspection ? <><div className="student-review-heading">{inspection.student.photo && <img src={inspection.student.photo} alt={`ID of ${inspection.student.name}`} />}<div><h3>{inspection.student.name}</h3><p className="small text-muted mb-0">{inspection.student.student_number}</p></div></div>
        <dl className="detail-list mb-3"><Detail label="College / school">{inspection.student.college}</Detail><Detail label="Email">{student?.email || "Not available"}</Detail><Detail label="Current minor offenses">{student?.offense_counts?.total_minor_offenses ?? "Not available"}</Detail><Detail label="Equivalent major offenses">{student?.offense_counts?.equivalent_major_offenses ?? "Not available"}</Detail></dl>
        <div className="suspected-box" id="detected-violation"><div className="d-flex justify-content-between mb-2"><span className="section-label">AI result - suspected</span><StatusBadge icon="camera">{inspection.ai_result}</StatusBadge></div>
          {inspection.violations.length ? <ul className="mb-0 ps-3 small">{inspection.violations.map((item,index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="small mb-0">No suspected violation detected. OSA review is still required.</p>}</div>
        <div className="decision-actions" aria-label="OSA decisions"><button id="btn-confirm-allow" className="btn btn-soft w-100" disabled={processing} onClick={() => choose("YES")}><Icon name="door-open" />Confirm Violation and Allow Entry</button>
          <button id="btn-no-violation" className="btn btn-outline-primary w-100" disabled={processing} onClick={() => choose("NO")}><Icon name="check2-circle" />No Violation</button>
          <button id="btn-confirm-deny" className="btn btn-primary w-100" disabled={processing} onClick={() => choose("DENY")}><Icon name="shield-x" />Confirm Violation and Deny Entry</button></div>
        <p className="small text-muted mb-0 mt-3" id="gate-status" role="status">{currentGate.error || gateMessage(currentGate.cycle)}</p>
      </> : <EmptyState icon="person-bounding-box" title="No student awaiting review" message="All three decisions become available after the backend receives an inspection." />}
    </div></section></div></div>
    {selection && <ConfirmDecisionModal selection={selection} busy={processing} error={error} onClose={() => setSelection(null)} onSubmit={submit} />}
  </>;
}

import { useEffect, useState } from "react";

export function gateCycleFinished(cycle, inspectionStatus) {
  if (!cycle || cycle.phase !== "CLOSED") return false;
  if (["WALKED_AWAY", "CANCELLED", "DENIED"].includes(cycle.outcome)) return true;
  return cycle.outcome === "ENTERED" &&
    ["PASS", "CLEARED", "VIOLATION CONFIRMED"].includes(inspectionStatus);
}

export function gateMessage(cycle) {
  if (!cycle) return "Waiting for gate status.";
  if (cycle.outcome === "DENIED") return "Entry denied by OSA. No official offense recorded.";
  if (cycle.phase === "CLOSED") {
    return cycle.outcome === "ENTERED"
      ? "Sensor confirmed entry. Gate cycle complete."
      : "Entry cancelled. No entry or final violation recorded.";
  }
  if (!cycle.connected) return `Gate connection lost. ${cycle.message || "Please ask the operator for assistance."}`;
  if (cycle.outcome === "UNCERTAIN") return "Passage was not confirmed. Please ask the operator for assistance.";
  if (cycle.message === "CLOSE_PAUSED") return "Gate closing paused. Please clear the passage.";
  if (cycle.phase === "WAITING_OSA") return "Gate closed. Waiting for AI inspection and OSA decision.";
  if (cycle.phase === "QUEUED" || cycle.phase === "SENT") return "OSA allowed entry. Waiting for gate acknowledgement.";
  if (cycle.phase === "OPENING") return "Gate opening. Please wait.";
  if (cycle.phase === "CLOSING") return "Passage completed. Gate closing.";
  return "Gate open. Please pass through.";
}

export default function useGateCycle(attemptId) {
  const [result, setResult] = useState(null);
  useEffect(() => {
    if (!attemptId) return undefined;
    let stopped = false;
    let timer;
    const abort = new AbortController();
    const poll = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/students/gate/attempts/${attemptId}/`,
          { signal: abort.signal },
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "Gate status unavailable.");
        if (!stopped) setResult({ attemptId, cycle: data, error: "" });
      } catch (error) {
        if (!stopped && error.name !== "AbortError") {
          setResult({ attemptId, cycle: null, error: "Gate status unavailable. Please ask the operator for assistance." });
        }
      } finally {
        if (!stopped) timer = setTimeout(poll, 500);
      }
    };
    poll();
    return () => {
      stopped = true;
      abort.abort();
      clearTimeout(timer);
    };
  }, [attemptId]);
  return result && result.attemptId === attemptId ? result : { cycle: null, error: "" };
}

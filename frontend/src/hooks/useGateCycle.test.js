import test from "node:test";
import assert from "node:assert/strict";
import { gateCycleFinished, gateMessage } from "./useGateCycle.js";

test("entry waits for both closed gate and completed inspection", () => {
  assert.equal(gateCycleFinished({ phase: "OPEN", outcome: "ENTERED" }, "PASS"), false);
  assert.equal(gateCycleFinished({ phase: "CLOSING", outcome: "ENTERED" }, "PASS"), false);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "ENTERED" }, "SCANNING..."), false);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "ENTERED" }, "AWAITING OSA CONFIRMATION"), false);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "ENTERED" }, "PASS"), true);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "ENTERED" }, "VIOLATION CONFIRMED"), true);
});

test("retreat clears the kiosk only after the gate has closed", () => {
  assert.equal(gateCycleFinished({ phase: "OPEN", outcome: "WALKED_AWAY" }, "PASS"), false);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "WALKED_AWAY" }, "SCANNING..."), true);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "CANCELLED" }, "SCANNING..."), true);
});

test("unknown or missing gate state never clears an active student", () => {
  assert.equal(gateCycleFinished(null, "PASS"), false);
  assert.equal(gateCycleFinished({ phase: "OPEN", outcome: "UNCERTAIN" }, "PASS"), false);
});

test("OSA pending and denial keep opening distinct from entry", () => {
  assert.match(gateMessage({ phase: "WAITING_OSA", connected: true }), /Gate closed/);
  assert.equal(gateCycleFinished({ phase: "WAITING_OSA", outcome: "PENDING" }, "PASS"), false);
  assert.match(gateMessage({ phase: "CLOSED", outcome: "DENIED" }), /denied/);
  assert.equal(gateCycleFinished({ phase: "CLOSED", outcome: "DENIED" }, "ENTRY DENIED"), true);
  assert.match(gateMessage({ phase: "SENT", connected: false }), /connection lost/);
});

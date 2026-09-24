import {
  useState,
  useEffect,
  useRef,
  useCallback
} from "react";

import { Link } from "react-router-dom";
import { StatusBadge, Icon, EmptyState, Detail } from "../components/UI";
import useGateCycle, { gateCycleFinished, gateMessage } from "../hooks/useGateCycle";


const OSA_DECISION_KEY =
  "sheseetv_osa_decision";


export default function StudentPage() {
  const [activeAttemptId, setActiveAttemptId] = useState(null);
  const [hardwareGate, setHardwareGate] = useState(false);
  const [gateNotice, setGateNotice] = useState("");
  const activeAttemptRef = useRef(null);
  const hardwareGateRef = useRef(false);
  const gateResettingRef = useRef(false);
  const scanInFlightRef = useRef(false);
  const gate = useGateCycle(hardwareGate ? activeAttemptId : null);


  const [currentTime, setCurrentTime] =
    useState(new Date());

  const [student, setStudent] =
    useState(null);

  const [cameraRunning, setCameraActive] =
    useState(false);

  const [cameraSession, setCameraSession] =
    useState(0);

  const [reportedScanStatus, setScanStatus] =
    useState("WAITING");

  const [detectedViolations, setViolations] =
    useState([]);

  const reviewStatus = gate.cycle?.confirmation_status;
  const reviewedLabel = { CONFIRMED_ALLOW: "VIOLATION CONFIRMED", REJECTED: "CLEARED", CONFIRMED_DENY: "ENTRY DENIED" }[reviewStatus];
  const scanStatus = reviewedLabel || reportedScanStatus;
  const cameraActive = cameraRunning && !reviewedLabel;
  const violations = reviewStatus === "REJECTED" ? [] : detectedViolations;

  const barcodeBuffer =
    useRef("");

  const lastKeyTime =
    useRef(0);

  const resettingRef =
    useRef(false);

  const osaDecisionHandledRef =
    useRef(false);


  // =====================================================
  // CLOCK
  // =====================================================

  useEffect(() => {

    const timer = setInterval(() => {

      setCurrentTime(
        new Date()
      );

    }, 1000);


    return () => {

      clearInterval(timer);

    };

  }, []);


  // =====================================================
  // CLEAR STUDENT PAGE
  // =====================================================

  const clearStudentPage = useCallback(() => {
    activeAttemptRef.current = null;
    hardwareGateRef.current = false;
    gateResettingRef.current = false;
    setActiveAttemptId(null);
    setHardwareGate(false);


    console.log(
      "Clearing previous student..."
    );


    setStudent(null);

    setCameraActive(false);

    setCameraSession(0);

    setScanStatus(
      "WAITING"
    );

    setViolations([]);


    // Reset barcode scanner
    barcodeBuffer.current = "";

    lastKeyTime.current =
      Date.now();


    // Reset frontend flags
    resettingRef.current =
      false;

    osaDecisionHandledRef.current =
      false;


    // Remove old OSA decision
    localStorage.removeItem(
      OSA_DECISION_KEY
    );


    console.log(
      "System ready for next ID scan."
    );

  }, []);


  // =====================================================
  // FORCE RESET FOR NEXT STUDENT
  // =====================================================
  //
  // Important:
  //
  // Even if Flask reset fails,
  // React will still reset so Attempt 2 is not blocked.
  //
  // =====================================================

  const prepareNextStudent = useCallback(async () => {

    console.log(
      "Preparing system for next student..."
    );


    try {

      const response = await fetch(
        "http://127.0.0.1:5000/reset-session",
        {
          method: "POST",
        }
      );


      if (response.ok) {

        const data =
          await response.json();


        console.log(
          "Flask reset response:",
          data
        );

      } else {

        console.error(
          "Flask reset returned:",
          response.status
        );

      }


    } catch (error) {

      console.error(
        "Flask reset failed:",
        error
      );

    }


    // ===============================================
    // ALWAYS CLEAR FRONTEND
    // ===============================================
    //
    // This is the important Attempt 2 fix.
    //
    // ===============================================

    clearStudentPage();


    console.log(
      "READY FOR NEXT ATTEMPT"
    );

  }, [clearStudentPage]);


  // =====================================================
  // START CAMERA
  // =====================================================

  const startCamera = useCallback(async (
    studentData,
    attemptId
  ) => {

    try {

      console.log(
        "Starting camera..."
      );


      const response = await fetch(
        "http://127.0.0.1:5000/start-camera",
        {
          method: "POST",

          headers: {

            "Content-Type":
              "application/json",

          },

          body: JSON.stringify({

            student_number:
              studentData.id,

            attempt_id:
              attemptId,

          }),

        }
      );


      const data =
        await response.json();


      if (String(activeAttemptRef.current) !== String(attemptId)) return false;

      console.log(
        "Start camera response:",
        data
      );


      if (
        response.ok &&
        data.success
      ) {

        // Force a brand-new MJPEG stream for every attempt.
        setCameraSession(
          Date.now()
        );

        setCameraActive(true);

        setScanStatus(
          "SCANNING..."
        );

        setViolations([]);


        return true;

      }


      setCameraActive(false);

      setScanStatus(
        "CAMERA ERROR"
      );


      return false;


    } catch (error) {

      console.error(
        "Camera start error:",
        error
      );


      setCameraActive(false);

      setScanStatus(
        "CAMERA ERROR"
      );


      return false;

    }

  }, []);


  // =====================================================
  // STOP CAMERA
  // =====================================================

  const stopCamera = useCallback(async () => {

    try {

      await fetch(
        "http://127.0.0.1:5000/stop-camera",
        {
          method: "POST",
        }
      );


    } catch (error) {

      console.error(
        "Camera stop error:",
        error
      );

    }


    setCameraActive(false);

  }, []);


  // =====================================================
  // DISPLAY STUDENT
  // =====================================================

  const displayStudent = useCallback(async (
    studentData,
    attemptId,
    usesHardwareGate = false
  ) => {
    activeAttemptRef.current = attemptId;
    hardwareGateRef.current = usesHardwareGate;
    gateResettingRef.current = false;
    setActiveAttemptId(attemptId);
    setHardwareGate(usesHardwareGate);
    setGateNotice("");


    // Remove previous decision
    localStorage.removeItem(
      OSA_DECISION_KEY
    );


    resettingRef.current =
      false;

    osaDecisionHandledRef.current =
      false;


    setStudent(
      studentData
    );


    setScanStatus(
      "SCANNING..."
    );


    setViolations([]);


    const cameraStarted =
      await startCamera(
        studentData,
        attemptId
      );


    if (!cameraStarted) {

      console.error(
        "Student loaded but camera failed."
      );

    }

  }, [startCamera]);


  // =====================================================
  // WATCH AI RESULT
  // =====================================================

  useEffect(() => {

    if (!student) {

      return;

    }


    const checkAIResult = async () => {

      try {

        const response = await fetch(
          "http://127.0.0.1:5000/inspection-result"
        );


        const data =
          await response.json();


        if (String(data.attempt_id) !== String(activeAttemptRef.current)) return;

        console.log(
          "AI result:",
          data
        );


        // ===============================================
        // OSA ALREADY DECIDED
        // ===============================================
        //
        // Do not allow old AI result to overwrite:
        //
        // VIOLATION CONFIRMED
        // CLEARED
        //
        // ===============================================

        if (
          osaDecisionHandledRef.current
        ) {

          return;

        }


        // ===============================================
        // AI STILL WORKING
        // ===============================================

        if (
          !data.finished
        ) {

          setScanStatus(
            "SCANNING..."
          );


          return;

        }


        // ===============================================
        // AI FINISHED
        // ===============================================

        setCameraActive(false);


        // ===============================================
        // VIOLATION
        // ===============================================

        if (
          data.status ===
          "VIOLATION"
        ) {

          setScanStatus(
            "AWAITING OSA CONFIRMATION"
          );


          setViolations(
            data.violations || []
          );


          return;

        }


        // ===============================================
        // PASS
        // ===============================================

        if (data.status === "PASS") {
          setScanStatus("AWAITING OSA CONFIRMATION");
          setViolations([]);
        }


      } catch (error) {

        console.error(
          "Inspection result error:",
          error
        );

      }

    };


    checkAIResult();


    const interval = setInterval(
      checkAIResult,
      1000
    );


    return () => {

      clearInterval(interval);

    };

  }, [student]);


  // =====================================================
  // WATCH OSA YES / NO
  // =====================================================

  useEffect(() => {

    if (!student) {

      return;

    }


    const checkOSADecision = () => {

      if (
        osaDecisionHandledRef.current
      ) {

        return;

      }


      const savedDecision =
        localStorage.getItem(
          OSA_DECISION_KEY
        );


      if (!savedDecision) {

        return;

      }


      try {

        const decisionData =
          JSON.parse(
            savedDecision
          );


        // ===============================================
        // MAKE SURE DECISION BELONGS TO CURRENT STUDENT
        // ===============================================

        if (
          String(
            decisionData.student_number
          ) !==
          String(
            student.id
          )
        ) {

          return;

        }


        if (String(decisionData.attempt_id) !== String(activeAttemptRef.current)) return;

        // ===============================================
        // OSA CLICKED YES
        // ===============================================

        if (
          decisionData.decision ===
          "YES"
        ) {

          console.log(
            "OSA CONFIRMED VIOLATION"
          );


          osaDecisionHandledRef.current =
            true;


          resettingRef.current =
            true;


          setCameraActive(false);


          setScanStatus(
            "VIOLATION CONFIRMED"
          );

        }


        // ===============================================
        // OSA CLICKED NO
        // ===============================================

        else if (
          decisionData.decision ===
          "NO"
        ) {

          console.log(
            "OSA CLEARED STUDENT"
          );


          osaDecisionHandledRef.current =
            true;


          resettingRef.current =
            true;


          setCameraActive(false);


          setScanStatus(
            "CLEARED"
          );


          setViolations([]);

        }


        else if (decisionData.decision === "DENY") {
          osaDecisionHandledRef.current = true;
          setCameraActive(false);
          setScanStatus("ENTRY DENIED");
        }
        else { return; }

        // ===============================================
        // SHOW RESULT THEN PREPARE ATTEMPT 2
        // ===============================================

        if (!hardwareGateRef.current) {
setTimeout(
          async () => {

            await prepareNextStudent();

          },
          2500
        );
        }


      } catch (error) {

        console.error(
          "OSA decision error:",
          error
        );

      }

    };


    // Check immediately
    checkOSADecision();


    // Then every half-second
    const interval = setInterval(
      checkOSADecision,
      500
    );


    return () => {

      clearInterval(interval);

    };

  }, [student, prepareNextStudent]);


  useEffect(() => {
    const status = gate.cycle?.confirmation_status;
    const label = { CONFIRMED_ALLOW: "VIOLATION CONFIRMED", REJECTED: "CLEARED",
      CONFIRMED_DENY: "ENTRY DENIED" }[status];
    if (label) {
      osaDecisionHandledRef.current = true;
    }
  }, [gate.cycle?.confirmation_status]);

  useEffect(() => {
    if (!hardwareGate || gateResettingRef.current ||
        !gateCycleFinished(gate.cycle, scanStatus)) return;
    gateResettingRef.current = true;
    setGateNotice(gate.cycle.outcome === "ENTERED"
      ? "Entry confirmed. Ready for the next ID."
      : gate.cycle.outcome === "DENIED" ? "Entry denied by OSA. No official offense recorded."
      : "Entry cancelled. No entry or final violation recorded.");
    prepareNextStudent();
  }, [hardwareGate, gate.cycle, scanStatus, prepareNextStudent]);


  // =====================================================
  // BARCODE SCANNER
  // =====================================================

  useEffect(() => {

    const handleScannerInput =
      async (event) => {

        const now =
          Date.now();


        // ===============================================
        // NEW BARCODE
        // ===============================================

        if (
          now -
          lastKeyTime.current >
          100
        ) {

          barcodeBuffer.current =
            "";

        }


        lastKeyTime.current =
          now;


        // ===============================================
        // ENTER = BARCODE COMPLETE
        // ===============================================

        if (
          event.key ===
          "Enter"
        ) {

          const barcode =
            barcodeBuffer.current.trim();


          barcodeBuffer.current =
            "";


          if (!barcode) {

            return;

          }


          // =============================================
          // BLOCK NEW STUDENT ONLY WHILE CURRENT
          // STUDENT IS ACTUALLY STILL ACTIVE
          // =============================================

          if (student || scanInFlightRef.current) {

            console.log(
              "Student currently being processed."
            );


            return;

          }


          scanInFlightRef.current = true;

          console.log(
            "Barcode scanned:",
            barcode
          );


          try {

            const response =
              await fetch(
                "http://127.0.0.1:8000/api/students/scan/",
                {
                  method: "POST",

                  headers: {

                    "Content-Type":
                      "application/json",

                  },

                  body:
                    JSON.stringify({

                      barcode:
                        barcode,

                    }),

                }
              );


            const data =
              await response.json();


            console.log(
              "Scan response:",
              data
            );


            // ===========================================
            // STUDENT FOUND
            // ===========================================

            if (
              data.success
            ) {

              resettingRef.current =
                false;


              osaDecisionHandledRef.current =
                false;


              await displayStudent(

                data.student,

                data.attempt_id,
                Boolean(data.hardware_gate)

              );

            }


            // ===========================================
            // STUDENT NOT FOUND
            // ===========================================

            else {

              clearStudentPage();
              setGateNotice(data.message || "ID could not be accepted.");
              if (!String(data.code || "").startsWith("GATE_")) await stopCamera();

            }


          } catch (error) {

            console.error(
              "Barcode scan error:",
              error
            );

          } finally {
            scanInFlightRef.current = false;
          }


          return;

        }


        // ===============================================
        // COLLECT NUMBERS
        // ===============================================

        if (
          /^[0-9]$/.test(
            event.key
          )
        ) {

          barcodeBuffer.current +=
            event.key;

        }

      };


    window.addEventListener(
      "keydown",
      handleScannerInput
    );


    return () => {

      window.removeEventListener(
        "keydown",
        handleScannerInput
      );

    };

  }, [student, displayStudent, clearStudentPage, stopCamera]);


  // =====================================================
  // CLEANUP WHEN PAGE CLOSES
  // =====================================================

  useEffect(() => {

    return () => {

      fetch(
        "http://127.0.0.1:5000/stop-camera",
        {
          method: "POST",
        }
      ).catch(
        () => {}
      );

    };

  }, []);


  // =====================================================
  // DATE
  // =====================================================

  const formattedDate =
    currentTime.toLocaleDateString(
      "en-US",
      {

        month:
          "long",

        day:
          "numeric",

        year:
          "numeric",

      }
    );


  // =====================================================
  // TIME
  // =====================================================

  const formattedTime =
    currentTime.toLocaleTimeString(
      "en-US",
      {

        hour:
          "2-digit",

        minute:
          "2-digit",

        second:
          "2-digit",

      }
    );


  // =====================================================
  // CAMERA MESSAGE
  // =====================================================

  const getCameraTitle = () => {
    if (scanStatus === "ENTRY DENIED") return "Entry Denied";

    if (
      scanStatus ===
      "VIOLATION CONFIRMED"
    ) {

      return "Violation Confirmed";

    }


    if (
      scanStatus ===
      "CLEARED"
    ) {

      return "Student Cleared";

    }


    if (
      scanStatus ===
      "PASS"
    ) {

      return "Dress Code Passed";

    }


    if (
      student &&
      scanStatus ===
      "AWAITING OSA CONFIRMATION"
    ) {

      return "Inspection Complete";

    }


    return "Camera Ready";

  };


  const getCameraMessage = () => {
    if (scanStatus === "ENTRY DENIED") return "Gate stays closed. No official offense recorded.";

    if (
      scanStatus ===
      "VIOLATION CONFIRMED"
    ) {

      return (
        "Dress code violation confirmed by OSA"
      );

    }


    if (
      scanStatus ===
      "CLEARED"
    ) {

      return (
        "No confirmed dress code violation"
      );

    }


    if (
      scanStatus ===
      "PASS"
    ) {

      return (
        "No dress code violation detected"
      );

    }


    if (
      student &&
      scanStatus ===
      "AWAITING OSA CONFIRMATION"
    ) {

      return (
        "Waiting for OSA confirmation"
      );

    }


    return (
      "Scan student ID to start camera"
    );

  };


  // =====================================================
  // PAGE
  // =====================================================

  return <div className="kiosk-shell container-fluid">
    <header className="kiosk-header"><div className="d-flex align-items-center gap-3"><span className="brand-mark"><Icon name="shield-check" /></span><div><h1>SHESEETVAI</h1><p className="small text-muted mb-0">Student dress-code scanner</p></div></div><div className="d-flex flex-wrap align-items-center gap-3"><span className="small text-muted">{formattedDate} | {formattedTime}</span><Link className="btn btn-outline-primary" to="/osa">OSA workspace</Link></div></header>
    <main className="row g-4"><section className="col-lg-8"><div className="card"><div className="card-body"><div className="d-flex justify-content-between align-items-center gap-2 mb-3"><h2 className="mb-0">Live camera</h2><StatusBadge icon="camera-video">{cameraActive ? "Inspecting" : "Camera idle"}</StatusBadge></div>
      <div className="media-frame" id="camera-preview">{cameraActive ? <img key={cameraSession} src={`http://127.0.0.1:5000/video_feed?session=${cameraSession}`} alt="Live dress-code inspection camera" /> : <EmptyState icon="upc-scan" title={getCameraTitle()} message={getCameraMessage()} />}</div>
      <div className="media-caption"><span><Icon name="upc-scan" />Scan a registered ID to begin</span><span>Wait for the OSA decision before entering</span></div></div></div></section>
    <aside className="col-lg-4"><div className="card mb-3"><div className="card-body"><h2>Student identity</h2>{student ? <><div className="student-review-heading">{student.photo && <img src={student.photo} alt={`ID of ${student.name}`} />}<div><h3>{student.name}</h3><p className="text-muted small mb-0">{student.id}</p></div></div><dl className="detail-list"><Detail label="School">{student.college}</Detail><Detail label="Attempt">{activeAttemptId}</Detail></dl></> : <EmptyState icon="person-badge" title="Waiting for ID scan" message="Use the connected barcode scanner." />}</div></div>
    <div className="card mb-3"><div className="card-body"><h2>Inspection status</h2><StatusBadge icon="clipboard-check" strong>{scanStatus}</StatusBadge><div className="mt-3 small">{violations.length ? <ul className="ps-3 mb-0">{violations.map((item,index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="text-muted mb-0">{student ? "No suspected types reported." : "Ready for a new student."}</p>}</div></div></div>
    <div className="card"><div className="card-body" role="status" aria-live="polite"><h2>Gate & passage</h2><p className="small mb-0">{hardwareGate ? gate.error || gateMessage(gate.cycle) : gateNotice || "No active gate attempt."}</p>{gate.cycle && <p className="small text-muted mt-2 mb-0">Sensor outcome: {gate.cycle.outcome.replaceAll("_", " ")}</p>}</div></div></aside></main>
  </div>;
}

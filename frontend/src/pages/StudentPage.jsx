import React, {
  useState,
  useEffect,
  useRef
} from "react";

import "../App.css";


const OSA_DECISION_KEY =
  "sheseetv_osa_decision";


export default function StudentPage() {

  const [currentTime, setCurrentTime] =
    useState(new Date());

  const [student, setStudent] =
    useState(null);

  const [cameraActive, setCameraActive] =
    useState(false);

  const [cameraSession, setCameraSession] =
    useState(0);

  const [scanStatus, setScanStatus] =
    useState("WAITING");

  const [violations, setViolations] =
    useState([]);

  const barcodeBuffer =
    useRef("");

  const lastKeyTime =
    useRef(Date.now());

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

  const clearStudentPage = () => {

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

  };


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

  const prepareNextStudent = async () => {

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

  };


  // =====================================================
  // START CAMERA
  // =====================================================

  const startCamera = async (
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

  };


  // =====================================================
  // STOP CAMERA
  // =====================================================

  const stopCamera = async () => {

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

  };


  // =====================================================
  // DISPLAY STUDENT
  // =====================================================

  const displayStudent = async (
    studentData,
    attemptId
  ) => {

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

  };


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

        if (
          data.status ===
          "PASS"
        ) {

          setScanStatus(
            "PASS"
          );


          setViolations([]);


          // Prevent multiple timers
          if (
            !resettingRef.current
          ) {

            resettingRef.current =
              true;


            setTimeout(
              async () => {

                await prepareNextStudent();

              },
              2500
            );

          }

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


        else {

          return;

        }


        // ===============================================
        // SHOW RESULT THEN PREPARE ATTEMPT 2
        // ===============================================

        setTimeout(
          async () => {

            await prepareNextStudent();

          },
          2500
        );


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

  }, [student]);


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

          if (student) {

            console.log(
              "Student currently being processed."
            );


            return;

          }


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

                data.attempt_id

              );

            }


            // ===========================================
            // STUDENT NOT FOUND
            // ===========================================

            else {

              clearStudentPage();


              await stopCamera();

            }


          } catch (error) {

            console.error(
              "Barcode scan error:",
              error
            );

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

  }, [student]);


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
  // STATUS CLASS
  // =====================================================

  const getStatusClass = () => {

    if (
      scanStatus ===
      "VIOLATION CONFIRMED"
    ) {

      return "approved violation-confirmed";

    }


    if (
      scanStatus ===
      "AWAITING OSA CONFIRMATION"
    ) {

      return "approved awaiting";

    }


    return "approved";

  };


  // =====================================================
  // STATUS COLOR
  // =====================================================

  const getStatusStyle = () => {

    // RED
    if (
      scanStatus ===
      "VIOLATION CONFIRMED"
    ) {

      return {

        backgroundColor:
          "#c21e1e",

        color:
          "white",

      };

    }


    // ORANGE
    if (
      scanStatus ===
      "AWAITING OSA CONFIRMATION"
    ) {

      return {

        backgroundColor:
          "#f0a000",

        color:
          "white",

      };

    }


    // GREEN
    if (
      scanStatus ===
      "CLEARED"
    ) {

      return {

        backgroundColor:
          "#18a848",

        color:
          "white",

      };

    }


    // NORMAL GREEN FROM CSS
    return {};

  };


  // =====================================================
  // CAMERA MESSAGE
  // =====================================================

  const getCameraTitle = () => {

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

  return (

    <div className="app">


      {/* =================================================
          HEADER
      ================================================= */}

      <header className="header">


        <div className="headerLeft">

          <div>

            <h1>
              SheSeeTV AI
            </h1>

            <p>
              Dress Code Compliance Scanner
            </p>

          </div>

        </div>


        <div className="dateTime">

          {formattedDate}

          {" | "}

          {formattedTime}

        </div>


      </header>



      {/* =================================================
          MAIN
      ================================================= */}

      <main className="mainLayout">


        {/* =================================================
            CAMERA
        ================================================= */}

        <section className="cameraCard">


          <div className="cameraBox">


            {cameraActive ? (

              <img

                key={cameraSession}

                src={`http://127.0.0.1:5000/video_feed?session=${cameraSession}`}

                className="cameraFeed"

                alt="Camera Feed"

                onLoad={() => {

                  console.log(
                    "Fresh camera stream loaded:",
                    cameraSession
                  );

                }}

                onError={() => {

                  console.log(
                    "Camera stream ended."
                  );

                }}

              />

            ) : (

              <div className="cameraPlaceholder">


                <h2>

                  {getCameraTitle()}

                </h2>


                <p>

                  {getCameraMessage()}

                </p>


              </div>

            )}


          </div>


        </section>



        {/* =================================================
            RIGHT PANEL
        ================================================= */}

        <aside className="rightPanel">


          {/* =================================================
              STUDENT ID
          ================================================= */}

          <div className="infoCard">


            <h2 className="studentIdTitle">

              Student ID

            </h2>


            <div className="studentIdContainer">


              {student ? (

                <div className="idPhoto scanned">


                  {student.photo ? (

                    <img
                      src={student.photo}
                      alt="Student ID"
                    />

                  ) : (

                    <div>

                      NO ID PHOTO

                    </div>

                  )}


                </div>

              ) : (

                <div className="idPhoto">

                  WAITING FOR SCAN

                </div>

              )}


            </div>


          </div>



          {/* =================================================
              DRESS CODE STATUS
          ================================================= */}

          <div className="resultCard">


            <h2>

              Dress Code Status

            </h2>


            <div
              className={
                getStatusClass()
              }
              style={
                getStatusStyle()
              }
            >

              {scanStatus}

            </div>


            <div className="violationBox">


              <h3>

                Violations

              </h3>


              {/* =============================================
                  WAITING
              ============================================= */}

              {!student && (

                <p>

                  Waiting for student

                </p>

              )}


              {/* =============================================
                  SCANNING
              ============================================= */}

              {student &&
              scanStatus ===
                "SCANNING..." && (

                <p>

                  Checking...

                </p>

              )}


              {/* =============================================
                  POSSIBLE / CONFIRMED VIOLATION
              ============================================= */}

              {student &&
              (
                scanStatus ===
                  "AWAITING OSA CONFIRMATION" ||

                scanStatus ===
                  "VIOLATION CONFIRMED"
              ) && (

                <div>


                  {violations.length > 0 ? (

                    violations.map(
                      (
                        violation,
                        index
                      ) => (

                        <p key={index}>

                          {violation}

                        </p>

                      )
                    )

                  ) : (

                    <p>

                      Possible violation detected

                    </p>

                  )}


                </div>

              )}


              {/* =============================================
                  PASS / CLEARED
              ============================================= */}

              {student &&
              (
                scanStatus ===
                  "PASS" ||

                scanStatus ===
                  "CLEARED"
              ) && (

                <p>

                  None

                </p>

              )}


            </div>


          </div>


        </aside>


      </main>


    </div>

  );

}
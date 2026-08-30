import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/ConfirmationPage.css";


const OSA_DECISION_KEY =
  "sheseetv_osa_decision";


function ConfirmationPage() {

  const [currentTime, setCurrentTime] =
    useState(new Date());

  const [rainyDays, setRainyDays] =
    useState(false);

  // Real AI inspection from Django
  const [inspection, setInspection] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [reviewing, setReviewing] =
    useState(false);

  const [message, setMessage] =
    useState("");


  // =====================================================
  // REAL-TIME CLOCK
  // =====================================================

  useEffect(() => {

    const timer = setInterval(() => {

      setCurrentTime(new Date());

    }, 1000);


    return () => {

      clearInterval(timer);

    };

  }, []);


  // =====================================================
  // GET PENDING AI INSPECTION
  // =====================================================

  const fetchPendingInspection = async () => {

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/api/students/ai-inspection/pending/"
      );


      const data =
        await response.json();


      console.log(
        "Pending AI inspection:",
        data
      );


      if (
        response.ok &&
        data.success
      ) {

        setInspection(
          data.inspection
        );

        setMessage("");

      } else {

        setInspection(null);

      }


    } catch (error) {

      console.error(
        "Failed to get pending AI inspection:",
        error
      );

    } finally {

      setLoading(false);

    }

  };


  // =====================================================
  // AUTOMATICALLY CHECK FOR NEW AI VIOLATION
  // =====================================================

  useEffect(() => {

    fetchPendingInspection();


    const interval = setInterval(() => {

      fetchPendingInspection();

    }, 2000);


    return () => {

      clearInterval(interval);

    };

  }, []);


  // =====================================================
  // OSA YES / NO
  // =====================================================

  const reviewInspection = async (
    decision
  ) => {

    if (!inspection) {

      return;

    }


    try {

      setReviewing(true);

      setMessage("");


      // Save these before setInspection(null)
      const studentNumber =
        inspection.student.student_number;

      const inspectionId =
        inspection.id;


      const response = await fetch(
        "http://127.0.0.1:8000/api/students/ai-inspection/review/",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({

            inspection_id:
              inspectionId,

            decision:
              decision,

          }),
        }
      );


      const data =
        await response.json();


      console.log(
        "OSA review response:",
        data
      );


      if (
        response.ok &&
        data.success
      ) {

        // ===============================================
        // SEND OSA DECISION TO STUDENT PAGE
        // ===============================================
        //
        // This happens ONLY after Django successfully
        // accepts and saves the OSA review.
        //
        // ===============================================

        localStorage.setItem(
          OSA_DECISION_KEY,
          JSON.stringify({

            student_number:
              studentNumber,

            decision:
              decision,

            inspection_id:
              inspectionId,

            timestamp:
              Date.now(),

          })
        );


        console.log(
          "OSA decision sent to Student Page:",
          decision
        );


        // ===============================================
        // YES
        // ===============================================

        if (
          decision ===
          "YES"
        ) {

          setMessage(
            "Violation confirmed."
          );

        }


        // ===============================================
        // NO
        // ===============================================

        else {

          setMessage(
            "AI detection rejected. Student cleared."
          );

        }


        // ===============================================
        // REMOVE REVIEWED INSPECTION
        // ===============================================

        setInspection(null);


        // ===============================================
        // CHECK FOR NEXT PENDING INSPECTION
        // ===============================================

        setTimeout(() => {

          fetchPendingInspection();

        }, 500);


      } else {

        setMessage(
          data.message ||
          "Unable to review inspection."
        );

      }


    } catch (error) {

      console.error(
        "OSA review error:",
        error
      );


      setMessage(
        "Could not connect to the server."
      );


    } finally {

      setReviewing(false);

    }

  };


  // =====================================================
  // DATE
  // =====================================================

  const formattedDate =
    currentTime.toLocaleDateString(
      "en-US",
      {
        month: "long",
        day: "numeric",
        year: "numeric",
      }
    );


  // =====================================================
  // TIME
  // =====================================================

  const formattedTime =
    currentTime.toLocaleTimeString(
      "en-US",
      {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      }
    );


  // =====================================================
  // PAGE
  // =====================================================

  return (
    <>

      <Sidebar />


      <div className="confirmation-page">


        {/* =================================================
            HEADER
        ================================================= */}

        <div className="confirmation-header">


          <div className="confirmation-title">

            <h1>
              Confirmation Page
            </h1>

            <p>
              Review the detected violation before confirming.
            </p>

          </div>


          <div className="confirmation-date">

            {formattedDate}
            {" | "}
            {formattedTime}

          </div>


        </div>


        {/* =================================================
            MAIN CONTENT
        ================================================= */}

        <div className="confirmation-container">


          {/* =================================================
              LEFT - CAPTURED AI PHOTO
          ================================================= */}

          <div className="photo-card">


            <h2>
              Captured Photo
            </h2>


            <div className="violation-photo">


              {inspection?.screenshot ? (

                <img
                  src={inspection.screenshot}
                  alt="AI detected violation"
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    borderRadius: "10px",
                  }}
                />

              ) : (

                <div className="photo-placeholder">


                  <div
                    style={{
                      fontSize: "50px"
                    }}
                  >
                    📷
                  </div>


                  <p>

                    {loading
                      ? "Checking for captured image..."
                      : "Waiting for captured image..."}

                  </p>


                </div>

              )}


            </div>


          </div>


          {/* =================================================
              RIGHT SIDE
          ================================================= */}

          <div className="confirmation-side">


            {/* =================================================
                RAINY DAYS
            ================================================= */}

            <div
              className={`rainy-days-card ${
                rainyDays
                  ? "rainy-on"
                  : "rainy-off"
              }`}
            >


              <div className="rainy-days-info">


                <h2>
                  Rainy Days
                </h2>


                <p>
                  Uniform leniency
                </p>


              </div>


              <label className="toggle-switch">


                <input
                  type="checkbox"
                  checked={rainyDays}
                  onChange={() =>
                    setRainyDays(
                      !rainyDays
                    )
                  }
                />


                <span className="toggle-slider">
                </span>


              </label>


            </div>


            {/* =================================================
                RAINY DAYS STATUS
            ================================================= */}

            <div
              className={
                rainyDays
                  ? "rainy-status active"
                  : "rainy-status"
              }
            >


              {rainyDays ? (

                <>

                  <strong>
                    Rainy Day Mode ON
                  </strong>

                  <span>
                    Civilian clothing and slippers are allowed.
                  </span>

                </>

              ) : (

                <>

                  <strong>
                    Rainy Day Mode OFF
                  </strong>

                  <span>
                    Regular uniform and dress code rules apply.
                  </span>

                </>

              )}


            </div>


            {/* =================================================
                STUDENT ID
            ================================================= */}

            <div className="student-id-card">


              <h2>
                Student ID
              </h2>


              <div className="student-id-image">


                {inspection?.student?.photo ? (

                  <img
                    src={
                      inspection.student.photo
                    }
                    alt="Student ID"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "contain",
                      borderRadius: "8px",
                    }}
                  />

                ) : (

                  <div className="id-placeholder">


                    <div
                      style={{
                        fontSize: "40px"
                      }}
                    >
                      🪪
                    </div>


                    <p>

                      {inspection
                        ? inspection.student.student_number
                        : "Student ID will appear here"}

                    </p>


                  </div>

                )}


              </div>


              {/* STUDENT NUMBER */}

              {inspection && (

                <div
                  style={{
                    textAlign: "center",
                    marginTop: "8px",
                    fontWeight: "600",
                  }}
                >

                  {inspection.student.student_number}

                </div>

              )}


            </div>


            {/* =================================================
                DETECTED VIOLATION
            ================================================= */}

            <div className="violation-card">


              <h2>
                Detected Violation
              </h2>


              {inspection ? (

                <>

                  <div className="violation-status">


                    <div className="status-label">
                      Possible Violation
                    </div>


                    <div className="status-value">


                      {inspection.violations &&
                      inspection.violations.length > 0 ? (

                        inspection.violations.map(
                          (
                            violation,
                            index
                          ) => (

                            <div key={index}>

                              {violation}

                            </div>

                          )
                        )

                      ) : (

                        <div>
                          Violation detected
                        </div>

                      )}


                    </div>


                  </div>


                  {/* =========================================
                      QUESTION
                  ========================================= */}

                  <div className="confirmation-question">


                    <h3>
                      Is this a violation?
                    </h3>


                    <div className="confirmation-buttons">


                      <button
                        className="confirmation-button no-button"
                        disabled={reviewing}
                        onClick={() =>
                          reviewInspection(
                            "NO"
                          )
                        }
                      >

                        {reviewing
                          ? "..."
                          : "NO"}

                      </button>


                      <button
                        className="confirmation-button yes-button"
                        disabled={reviewing}
                        onClick={() =>
                          reviewInspection(
                            "YES"
                          )
                        }
                      >

                        {reviewing
                          ? "..."
                          : "YES"}

                      </button>


                    </div>


                  </div>

                </>

              ) : (

                <div className="violation-status">


                  <div className="status-label">

                    {loading
                      ? "Checking..."
                      : "No Pending Violation"}

                  </div>


                  <div className="status-value">

                    Waiting for AI detection

                  </div>


                </div>

              )}


              {/* =================================================
                  REVIEW MESSAGE
              ================================================= */}

              {message && (

                <div
                  style={{
                    marginTop: "12px",
                    textAlign: "center",
                    fontWeight: "600",
                  }}
                >

                  {message}

                </div>

              )}


            </div>


          </div>


        </div>


      </div>

    </>
  );
}


export default ConfirmationPage;
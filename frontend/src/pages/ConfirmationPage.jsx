import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/ConfirmationPage.css";

function ConfirmationPage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [rainyDays, setRainyDays] = useState(false);

  // Real-time clock
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formattedDate = currentTime.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const formattedTime = currentTime.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <>
      <Sidebar />

      <div className="confirmation-page">

        {/* HEADER */}
        <div className="confirmation-header">

          <div className="confirmation-title">
            <h1>Confirmation Page</h1>
            <p>
              Review the detected violation before confirming.
            </p>
          </div>

          <div className="confirmation-date">
            {formattedDate} | {formattedTime}
          </div>

        </div>


        {/* MAIN CONTENT */}
        <div className="confirmation-container">

          {/* =====================================
              LEFT - CAPTURED PHOTO
          ===================================== */}
          <div className="photo-card">

            <h2>Captured Photo</h2>

            <div className="violation-photo">

              <div className="photo-placeholder">

                <div style={{ fontSize: "50px" }}>
                  📷
                </div>

                <p>
                  Waiting for captured image...
                </p>

              </div>

            </div>

          </div>


          {/* =====================================
              RIGHT SIDE
          ===================================== */}
          <div className="confirmation-side">


            {/* =====================================
                RAINY DAYS
            ===================================== */}
            <div
              className={`rainy-days-card ${
                rainyDays ? "rainy-on" : "rainy-off"
              }`}
            >

              <div className="rainy-days-info">

                <h2>Rainy Days</h2>

                <p>
                  Uniform leniency
                </p>

              </div>


              {/* TOGGLE */}
              <label className="toggle-switch">

                <input
                  type="checkbox"
                  checked={rainyDays}
                  onChange={() => setRainyDays(!rainyDays)}
                />

                <span className="toggle-slider"></span>

              </label>

            </div>


            {/* =====================================
                RAINY DAYS STATUS
            ===================================== */}
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


            {/* =====================================
                STUDENT ID
            ===================================== */}
            <div className="student-id-card">

              <h2>Student ID</h2>

              <div className="student-id-image">

                <div className="id-placeholder">

                  <div style={{ fontSize: "40px" }}>
                    🪪
                  </div>

                  <p>
                    Student ID will appear here
                  </p>

                </div>

              </div>

            </div>


            {/* =====================================
                DETECTED VIOLATION
            ===================================== */}
            <div className="violation-card">

              <h2>Detected Violation</h2>

              <div className="violation-status">

                <div className="status-label">
                  Possible Violation
                </div>

                <div className="status-value">
                  Midriff Exposure
                </div>

              </div>


              {/* QUESTION */}
              <div className="confirmation-question">

                <h3>
                  Is this a violation?
                </h3>

                <div className="confirmation-buttons">

                  <button
                    className="confirmation-button no-button"
                  >
                    NO
                  </button>

                  <button
                    className="confirmation-button yes-button"
                  >
                    YES
                  </button>

                </div>

              </div>

            </div>

          </div>

        </div>

      </div>
    </>
  );
}

export default ConfirmationPage;
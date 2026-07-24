import React, { useState, useEffect } from "react";
import "../App.css";
import hauLogo from "../assets/hau-logo.png";

export default function StudentPage() {
  const [currentTime, setCurrentTime] = useState(new Date());

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
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="studentPage">
      <header className="header">
        <div className="headerLeft">
          <img
            src={hauLogo}
            alt="HAU Logo"
            className="hauLogo"
          />

          <div>
            <h1>Holy Angel University</h1>
            <p>SheSeeTV AI: Dress Code Compliance Scanner</p>
          </div>
        </div>

        <div className="dateTime">
          {formattedDate} | {formattedTime}
        </div>
      </header>

      <main className="mainLayout">
        {/* CAMERA */}
        <section className="cameraCard">
          <div className="cameraBox">
            <img
              src="http://127.0.0.1:5000/video_feed"
              className="cameraFeed"
              alt="Camera Feed"
            />
          </div>
        </section>

        {/* RIGHT PANEL */}
        <aside className="rightPanel">

          {/* STUDENT ID */}
          <div className="infoCard">
            <h2 className="studentIdTitle">Student ID</h2>

            <div className="studentIdContainer">

              {/* Previous Scan */}
              <div className="idPhoto">
                PHOTO
              </div>

              {/* Current Scan */}
              <div className="idPhoto current">
                PHOTO
              </div>

            </div>
          </div>

          {/* RESULT */}
          <div className="resultCard">
            <h2>Dress Code Status</h2>

            <div className="approved">
              ✔ ACCESS GRANTED
            </div>

            <div className="violationBox">
              <h3>Violations</h3>
              <p>✔ None</p>
            </div>
          </div>

        </aside>
      </main>
    </div>
  );
}
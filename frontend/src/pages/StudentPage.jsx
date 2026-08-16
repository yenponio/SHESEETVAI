import React, { useState, useEffect, useRef } from "react";
import "../App.css";

export default function StudentPage() {

  const [currentTime, setCurrentTime] = useState(new Date());

  const [student, setStudent] = useState(null);

  // Barcode scanner input
  const barcodeBuffer = useRef("");

  const lastKeyTime = useRef(Date.now());


  // =====================================================
  // CLOCK
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
  // DISPLAY STUDENT
  // =====================================================

  const displayStudent = (data) => {

    setStudent(data);


    // Clear student after 10 seconds

    setTimeout(() => {

      setStudent(null);

    }, 10000);

  };


  // =====================================================
  // BARCODE SCANNER
  // =====================================================

  useEffect(() => {

    const handleScannerInput = async (event) => {

      const now = Date.now();


      // -------------------------------------------------
      // Detect new barcode
      // -------------------------------------------------

      if (now - lastKeyTime.current > 100) {

        barcodeBuffer.current = "";

      }


      lastKeyTime.current = now;


      // =================================================
      // ENTER = BARCODE FINISHED
      // =================================================

      if (event.key === "Enter") {

        const barcode =
          barcodeBuffer.current.trim();


        barcodeBuffer.current = "";


        if (!barcode) {

          return;

        }


        console.log(
          "Barcode scanned:",
          barcode
        );


        try {

          // =================================================
          // SEND BARCODE TO DJANGO
          // =================================================

          const response = await fetch(

            "http://127.0.0.1:8000/api/students/scan/",

            {

              method: "POST",

              headers: {

                "Content-Type": "application/json",

              },

              body: JSON.stringify({

                barcode: barcode,

              }),

            }

          );


          const data =
            await response.json();


          console.log(
            "Scan response:",
            data
          );


          // =================================================
          // STUDENT FOUND
          // =================================================

          if (data.success) {

            console.log(
              "Student found:",
              data.student
            );


            console.log(
              "ID photo:",
              data.student.photo
            );


            displayStudent(
              data.student
            );

          }


          // =================================================
          // STUDENT NOT FOUND
          // =================================================

          else {

            console.log(
              "Student not found:",
              data.message
            );


            setStudent(null);

          }


        }

        catch (error) {

          console.error(
            "Barcode scan error:",
            error
          );

        }


        return;

      }


      // =================================================
      // COLLECT NUMBERS ONLY
      // =================================================

      if (/^[0-9]$/.test(event.key)) {

        barcodeBuffer.current +=
          event.key;


        console.log(
          "Scanner buffer:",
          barcodeBuffer.current
        );

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

  }, []);


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

        hour: "2-digit",

        minute: "2-digit",

        second: "2-digit",

      }

    );


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

            <img

              src="http://127.0.0.1:5000/video_feed"

              className="cameraFeed"

              alt="Camera Feed"

            />

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

                /* -----------------------------------------
                   SCANNED STUDENT
                ----------------------------------------- */

                <div

                  className="idPhoto scanned"

                >

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

                /* -----------------------------------------
                   WAITING FOR SCAN
                ----------------------------------------- */

                <div

                  className="idPhoto"

                >

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


            <div className="approved">

              {student

                ? "✔ ACCESS GRANTED"

                : "WAITING"

              }

            </div>


            <div className="violationBox">

              <h3>

                Violations

              </h3>


              <p>

                ✔ None

              </p>

            </div>

          </div>


        </aside>


      </main>


    </div>

  );

}
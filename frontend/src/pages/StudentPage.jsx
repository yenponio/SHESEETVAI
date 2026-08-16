import React, { useState, useEffect } from "react";
import "../App.css";


export default function StudentPage() {

  const [currentTime, setCurrentTime] = useState(new Date());
  const [student, setStudent] = useState(null);
  const [clearTimer, setClearTimer] = useState(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const displayStudent = (data) => {
    setStudent(data);

    if (clearTimer) {
      clearTimeout(clearTimer);
    }

    const timer = setTimeout(() => {
      setStudent(null);
    }, 10000);

    setClearTimer(timer);
  };

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
useEffect(() => {

    const checkScan = setInterval(async()=>{

        try{

            const response = await fetch(
                "http://127.0.0.1:8000/api/students/scan/latest/"
            );

            const data = await response.json();

            if(data.success){

                setStudent(data.student);
                setTimeout(()=>{

                    setStudent(null);

                },5000);
            }
            

        }catch(error){

            console.log(error);

        }


    },1000);


    return ()=>clearInterval(checkScan);


},[]);
  return (
    <div className="app">

      <header className="header">

        <div className="headerLeft">

          

          <div>
            <h1>SheSeeTV AI</h1>
            <p> Dress Code Compliance Scanner</p>
          </div>

        </div>


        <div className="dateTime">
          {formattedDate} | {formattedTime}
        </div>

      </header>


      <main className="mainLayout">

        <section className="cameraCard">
          <div className="cameraBox">
            <img
              src="http://127.0.0.1:5000/video_feed"
              className="cameraFeed"
              alt="Camera Feed"
            />
          </div>
        </section>


        <aside className="rightPanel">

          <div className="infoCard">

            <h2 className="studentIdTitle">
              Student ID
            </h2>

            <div className="studentIdContainer">

              {student ? (
                <>
                  <div className="idPhoto">
                    {student.photo}
                  </div>

                  <div className="studentInfo">
                    <h3>{student.name}</h3>
                    <p>ID: {student.id}</p>
                    <p>Time: {student.time}</p>
                  </div>
                </>
              ) : (
                <div className="idPhoto">
                  WAITING FOR SCAN
                </div>
              )}

            </div>

          </div>


          <div className="resultCard">

            <h2>Dress Code Status</h2>

            <div className="approved">
              {student ? "✔ ACCESS GRANTED" : "WAITING"}
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
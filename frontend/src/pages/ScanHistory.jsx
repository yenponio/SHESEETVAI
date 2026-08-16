import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import "../styles/Dashboard.css";
import { useNavigate } from "react-router-dom";

function ScanHistory() {
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {

    async function fetchLogs() {

      try {

        const response = await fetch(
          "http://127.0.0.1:8000/api/students/dashboard/"
        );

        const data = await response.json();

        setLogs(data.recent_logs);

      } catch (error) {

        console.error(
          "Scan history error:",
          error
        );

      }

    }


    fetchLogs();

  }, []);



  const filteredLogs = logs.filter((student) =>

    student.studentNumber
      .toLowerCase()
      .includes(search.toLowerCase())

    ||

    student.name
      .toLowerCase()
      .includes(search.toLowerCase())

    ||

    student.college
      .toLowerCase()
      .includes(search.toLowerCase())

  );



  return (

    <>
      <Sidebar />

      <div className="dashboard">


       <div className="dashboard-header">

        <h1>
          Scan History
        </h1>

        <button
          onClick={() => navigate("/dashboard")}
          className="back-button"
        >
          ← Back to Dashboard
        </button>

      </div>



        <div className="search-container">

          <input
            type="text"
            placeholder="Search student..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

        </div>



        <div className="table-card">


          <h2>
            All Entry Records
          </h2>



          <table>

            <thead>

              <tr>
                <th>Student Number</th>
                <th>Name</th>
                <th>College</th>
                <th>Status</th>
                <th>Time</th>
              </tr>

            </thead>



            <tbody>

              {filteredLogs.length > 0 ? (

                filteredLogs.map((student,index)=>(

                  <tr key={index}>

                    <td>
                      {student.studentNumber}
                    </td>


                    <td>
                      {student.name}
                    </td>


                    <td>
                      {student.college}
                    </td>


                    <td
                      className={
                        student.status === "Access Granted"
                        ? "granted"
                        : "violation"
                      }
                    >
                      {student.status}
                    </td>


                    <td>
                      {student.time}
                    </td>

                  </tr>

                ))

              ) : (

                <tr>
                  <td colSpan="5">
                    No records found
                  </td>
                </tr>

              )}

            </tbody>


          </table>


        </div>


      </div>

    </>

  );

}


export default ScanHistory;
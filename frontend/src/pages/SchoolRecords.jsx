import "./../styles/Records.css";
import Sidebar from "../components/Sidebar";
import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

function SchoolRecords() {

  const { school } = useParams();
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);

  useEffect(() => {

    fetch(`http://127.0.0.1:8000/api/students/records/${school}/`)
      .then(res => res.json())
      .then(data => setRecords(data.records))
      .catch(err => console.error("School records error:", err));

  }, [school]);


  return (
    <>
      <Sidebar />

      <div className="records-page">

        <button 
          className="back-btn"
          onClick={() => navigate("/records")}
        >
          ← Back to Schools
        </button>

        <h1>{school.toUpperCase()} Records</h1>

        <p className="subtitle">
          Students with dress code violations
        </p>


        <div className="summary-card">

          <div>
            <h3>{records.length}</h3>
            <p>Students Violated</p>
          </div>

          <div>
            <h3>{new Date().toLocaleDateString()}</h3>
            <p>Last Updated</p>
          </div>

        </div>



        <div className="recent-card">

          <table>

            <thead>
              <tr>
                <th>Student No.</th>
                <th>Name</th>
                <th>Violation Count</th>
                <th>Status</th>
              </tr>
            </thead>


            <tbody>

              {records.map((student,index)=>(

                <tr key={index}>

                  <td>{student.studentNumber}</td>

                  <td>{student.name}</td>

                  <td>{student.violations}</td>

                  <td className="violation">
                    {student.status}
                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        </div>

      </div>
    </>
  );
}

export default SchoolRecords;
import "./../styles/Records.css";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

function Records() {

  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/students/records/")
      .then(res => res.json())
      .then(data => setRecords(data.records))
      .catch(err => console.error("Records error:", err));
  }, []);


  const schools = [
    "SEA",
    "SOC",
    "SHTM",
    "SBA",
    "SED",
    "CCJF",
    "SAS",
    "SNAMS"
  ];


  const filteredRecords = records.filter(student => {
  const keyword = search.toLowerCase();
  return (
      student.violations > 0 &&
      (
        student.studentNumber.toLowerCase().includes(keyword) ||
        student.name.toLowerCase().includes(keyword) ||
        student.college.toLowerCase().includes(keyword)
      )
    );
});


  return (
    <>
      <Sidebar />

      <div className="records-page">

        <h1>Dress Code Records</h1>

        <p className="subtitle">
          Select a school to view students with dress code violations.
        </p>


        <div className="school-grid">

          {schools.map(school => (

            <div
              key={school}
              className="school-card"
              onClick={() => navigate(`/records/${school.toLowerCase()}`)}
            >

              <h2>{school}</h2>

              <p>View violation records</p>

              <span>
              {
              records.filter(
                student =>
                student.college === school &&
                student.violations > 0
              ).length
              } Students Violated
              </span>

            </div>

          ))}

        </div>



        <div className="recent-card">

          <div className="recent-header">

            <h2>Recent Violations</h2>

            <input
              type="text"
              placeholder="Search student..."
              value={search}
              onChange={(e)=>setSearch(e.target.value)}
            />

          </div>


          <table>

            <thead>
              <tr>
                <th>Student No.</th>
                <th>Name</th>
                <th>School</th>
                <th>Violation Count</th>
                <th>Status</th>
              </tr>
            </thead>


            <tbody>

              {filteredRecords.map((student,index)=>(

                <tr key={index}>

                  <td>{student.studentNumber}</td>

                  <td>{student.name}</td>

                  <td>{student.college}</td>

                  <td>{student.violations}</td>

                  <td className={
                    student.status === "Clear"
                    ? "clear"
                    : "violation"
                  }>
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

export default Records;
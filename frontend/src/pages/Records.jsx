import "./../styles/Records.css";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";

function Records() {
  const navigate = useNavigate();

  const schools = [
    { code: "SEA", name: "School of Engineering and Architecture", today: 15 },
    { code: "SOC", name: "School of Computing", today: 8 },
    { code: "SHTM", name: "School of Hospitality and Tourism Management", today: 21 },
    { code: "SBA", name: "School of Business and Accountancy", today: 5 },
    { code: "SED", name: "School of Education", today: 3 },
    { code: "CCJF", name: "College of Criminal Justice Education and Forensics ", today: 11 },
    { code: "SAS", name: "School of Arts and Sciences", today: 7 },
    { code: "SNAMS", name: "School of Nursing and Allied Medical Sciences ", today: 7 },

  ];

  const violations = [
    {
      studentNo: "20951987",
      name: "Ponio, Jennesie Erin L.",
      school: "SEA",
      violation: "Slippers",
      time: "8:02 AM",
    },
    {
      studentNo: "20969752",
      name: "Ishii, Yuichiro L.",
      school: "SOC",
      violation: "No ID",
      time: "8:15 AM",
    },
    {
      studentNo: "20957815",
      name: "Muldong, Geyser Ardin S.",
      school: "SEA",
      violation: "Long Hair",
      time: "9:10 AM",
    },
  ];

  return (
    <>
      <Sidebar />

      <div className="records-page">
        <h1>Dress Code Records</h1>

        <p className="subtitle">
          Select a school to view its complete violation records.
        </p>

        <div className="school-grid">
          {schools.map((school) => (
            <div
              key={school.code}
              className="school-card"
              onClick={() =>
                navigate(`/records/${school.code.toLowerCase()}`)
              }
            >
              <h2>{school.code}</h2>
              <p>{school.name}</p>

              <span>{school.today} Today</span>
            </div>
          ))}
        </div>

        <div className="recent-card">
          <div className="recent-header">
            <h2>Recent Violations</h2>

            <input
              type="text"
              placeholder="Search student..."
            />
          </div>

          <table>
            <thead>
              <tr>
                <th>Student No.</th>
                <th>Name</th>
                <th>School</th>
                <th>Violation</th>
                <th>Time</th>
              </tr>
            </thead>

            <tbody>
              {violations.map((item, index) => (
                <tr key={index}>
                  <td>{item.studentNo}</td>
                  <td>{item.name}</td>
                  <td>{item.school}</td>
                  <td>{item.violation}</td>
                  <td>{item.time}</td>
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
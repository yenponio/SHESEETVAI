import { useState } from "react";
import Sidebar from "../components/Sidebar";

function Students() {
  const [search, setSearch] = useState("");

  const students = [
    {
      studentNumber: "20951987",
      name: "Ponio, Jennesie Erin L.",
      college: "School of Engineering and Architecture",
    },
    {
      studentNumber: "20969752",
      name: "Ishii, Yuichiro L.",
      college: "School of Engineering and Architecture",
    },
    {
      studentNumber: "20957815",
      name: "Muldong, Geyser Ardin S.",
      college: "School of Engineering and Architecture",
    },
  ];

  const filteredStudents = students.filter(
    (student) =>
      student.name.toLowerCase().includes(search.toLowerCase()) ||
      student.studentNumber.includes(search)
  );

  return (
    <>
      <Sidebar />

      <div
        style={{
          marginLeft: "70px",
          padding: "40px",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <h1 style={{ color: "#800000" }}>Student Database</h1>

        <input
          type="text"
          placeholder="🔍 Search by Student Number or Name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "400px",
            padding: "12px",
            fontSize: "16px",
            marginTop: "20px",
            marginBottom: "25px",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        />

        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "#fff",
          }}
        >
          <thead
            style={{
              background: "#800000",
              color: "white",
            }}
          >
            <tr>
              <th style={{ padding: "15px" }}>Student Number</th>
              <th style={{ padding: "15px" }}>Name</th>
              <th style={{ padding: "15px" }}>College</th>
            </tr>
          </thead>

          <tbody>
            {filteredStudents.length > 0 ? (
              filteredStudents.map((student, index) => (
                <tr
                  key={index}
                  style={{
                    borderBottom: "1px solid #ddd",
                    textAlign: "center",
                  }}
                >
                  <td style={{ padding: "12px" }}>{student.studentNumber}</td>
                  <td style={{ padding: "12px" }}>{student.name}</td>
                  <td style={{ padding: "12px" }}>{student.college}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan="3"
                  style={{
                    padding: "20px",
                    textAlign: "center",
                    color: "gray",
                  }}
                >
                  No student found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default Students;
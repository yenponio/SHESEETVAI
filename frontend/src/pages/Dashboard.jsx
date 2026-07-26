import "./../styles/Dashboard.css";
import { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";

import SearchBar from "../components/dashboard/SearchBar";
import StatCard from "../components/dashboard/StatCard";
import CollegeChart from "../components/dashboard/CollegeChart";
import ComplianceChart from "../components/dashboard/ComplianceChart";
import {
  FaUserGraduate,
  FaClock,
  FaCalendarAlt,
} from "react-icons/fa";

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);

  const students = [
    {
      studentNumber: "20969752",
      name: "Ishii, Yuichiro L.",
      college: "CCJEF",
      status: "Access Granted",
    },
    {
      studentNumber: "20957815",
      name: "Muldong, Geyser Ardin S.",
      college: "SEA",
      status: "Dress Code Violation",
    },
    {
      studentNumber: "20950773",
      name: "Santos, Raynier Ronn G.",
      college: "SHTM",
      status: "Access Granted",
    },
    {
      studentNumber: "20952281",
      name: "Cayanan, Jerica Therese F.",
      college: "SE",
      status: "Access Granted",
    },
    {
      studentNumber: "20959288",
      name: "Jose, Chloe Lane B.",
      college: "SC",
      status: "Dress Code Violation",
    },
    {
      studentNumber: "20550881",
      name: "Punsalan, Jeneveve S.",
      college: "SNAMS",
      status: "Access Granted",
    },
    {
      studentNumber: "20968222",
      name: "Tapnio, Patricia Lei R.",
      college: "SAS",
      status: "Dress Code Violation",
    },
    {
      studentNumber: "20951987",
      name: "Ponio, Jennesie Erin L.",
      college: "SBA",
      status: "Access Granted",
    },
  ];

  useEffect(() => {
    async function fetchDashboard() {
      const response = await fetch(
        "http://127.0.0.1:8000/api/students/dashboard/"
      );

      const data = await response.json();

      console.log(data);

      setDashboardData(data);
    }

    fetchDashboard();
  }, []);

  return (
    <>
      <Sidebar />

      <div className="dashboard">
        <div className="dashboard-header">
          <h1>OSA Dashboard</h1>
        </div>

        <SearchBar />

        <div className="stats-container">
          <StatCard
            title="Students Today"
            value={dashboardData ? dashboardData.total_students : "Loading..."}
            icon={<FaUserGraduate />}
          />

          <StatCard
            title="Average Scan Time"
            value="2.4 sec"
            icon={<FaClock />}
          />

          <StatCard
            title="Semester Day"
            value="35"
            icon={<FaCalendarAlt />}
          />
        </div>

        <div className="charts-container">
          <div className="chart-card">
            <CollegeChart />
          </div>

          <div className="chart-card">
            <ComplianceChart />
          </div>
        </div>

        <div className="table-card">
          <h2>Recent Scan Logs</h2>

          <table>
            <thead>
              <tr>
                <th>Student Number</th>
                <th>Name</th>
                <th>College</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {students.map((student, index) => (
                <tr key={index}>
                  <td>{student.studentNumber}</td>
                  <td>{student.name}</td>
                  <td>{student.college}</td>
                  <td
                    className={
                      student.status === "Access Granted"
                        ? "granted"
                        : "violation"
                    }
                  >
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

export default Dashboard;
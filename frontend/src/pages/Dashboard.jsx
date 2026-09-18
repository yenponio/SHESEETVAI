import "./../styles/Dashboard.css";
import { useState } from "react";
import useLiveData from "../hooks/useLiveData";
import Sidebar from "../components/Sidebar";
import { useNavigate } from "react-router-dom";
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
  const navigate = useNavigate();
  const { data: dashboardData, error } = useLiveData("http://127.0.0.1:8000/api/students/dashboard/");
  const [search, setSearch] = useState("");


  const filteredLogs =
    dashboardData?.recent_logs.filter((student) =>
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

    ) || [];



  return (

    <>
      <Sidebar />

      <div className="dashboard">


        <div className="dashboard-header">
          <h1>OSA Dresscode Violation Tracker</h1>
        </div>


        {error && <p role="alert">{error}</p>}

        <SearchBar
          search={search}
          setSearch={setSearch}
        />



        {/* STAT CARDS */}
        <div className="stats-container">

          <StatCard
            title="STUDENTS TODAY"
            value={
              dashboardData
                ? dashboardData.students_today
                : "Loading..."
            }
            icon={<FaUserGraduate />}
          />


          <StatCard
            title="AVERAGE SCAN TIME"
            value={
              dashboardData
                ? dashboardData.average_scan_time
                : "Loading..."
            }
            icon={<FaClock />}
          />


          <StatCard
            title="VIOLATION RECORDS (ALL TIME)"
            value={dashboardData ? dashboardData.total_violations : "Loading..."}
            icon={<FaCalendarAlt />}
          />

        </div>



        {/* CHARTS */}
        <div className="charts-container">
          {!dashboardData ? <p>{error ? "Charts are unavailable." : "Loading charts..."}</p> : <>


          <div className="chart-card">

            <CollegeChart
              data={
                dashboardData?.college_chart || []
              }
            />

          </div>



          <div className="chart-card">

            <ComplianceChart data={dashboardData?.compliance_chart || []} />

          </div>


          </>}
        </div>




        {/* RECENT LOGS */}
        <div className="table-card">


          <div className="table-header">

            <h2>
              Recent Scan Logs
            </h2>


            <button
              onClick={() => navigate("/scan-history")}
            >
              View All Logs
            </button>

          </div>



          {!dashboardData && (
            <p>
              Loading dashboard...
            </p>
          )}



          {dashboardData && (

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
                          student.status === "No Violation"
                            ? "granted"
                            : "violation"
                        }
                      >
                        {student.status}
                      </td>

                    </tr>

                  ))

                ) : (

                  <tr>

                    <td colSpan="4">
                      No student found
                    </td>

                  </tr>

                )}

              </tbody>


            </table>

          )}


        </div>


      </div>

    </>

  );

}


export default Dashboard;
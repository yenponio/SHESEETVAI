import "./../styles/Records.css";
import Sidebar from "../components/Sidebar";
import ViolationTable from "../components/ViolationTable";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import useLiveData from "../hooks/useLiveData";

function Records() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const { data, error } = useLiveData("http://127.0.0.1:8000/api/students/records/");
  const records = data?.records || [];
  const keyword = search.trim().toLowerCase();
  const filteredRecords = records.filter(record =>
    [record.studentNumber, record.name, record.college, record.collegeName,
      record.violationType, record.date, record.time]
      .some(value => value.toLowerCase().includes(keyword))
  );

  return (
    <>
      <Sidebar />
      <div className="records-page">
        <h1>Dress Code Records</h1>
        <p className="subtitle">All-time violation reports. Select a school to view its records.</p>
        {error && <p role="alert">{error}</p>}
        <div className="school-grid">
          {(data?.schools || []).map(school => (
            <div key={school} className="school-card"
              onClick={() => navigate(`/records/${encodeURIComponent(school.toLowerCase())}`)}>
              <h2>{school}</h2>
              <p>View violation records</p>
              <span>{records.filter(record => record.college === school).length} Violation Records</span>
            </div>
          ))}
        </div>
        <div className="recent-card">
          <div className="recent-header">
            <h2>Violation Records</h2>
            <input type="text" placeholder="Search records..." value={search}
              onChange={event => setSearch(event.target.value)} />
          </div>
          {data && <p>Showing {filteredRecords.length} of {data.total} violation records (all time)</p>}
          <ViolationTable records={filteredRecords} loading={!data && !error} error={error} />
        </div>
      </div>
    </>
  );
}

export default Records;

import "./../styles/Records.css";
import Sidebar from "../components/Sidebar";
import ViolationTable from "../components/ViolationTable";
import { useParams, useNavigate } from "react-router-dom";
import useLiveData from "../hooks/useLiveData";

function SchoolRecords() {
  const { school } = useParams();
  const navigate = useNavigate();
  const { data, error, updatedAt } = useLiveData(
    `http://127.0.0.1:8000/api/students/records/${encodeURIComponent(school)}/`
  );

  return (
    <>
      <Sidebar />
      <div className="records-page">
        <button className="back-btn" onClick={() => navigate("/records")}>Back to Schools</button>
        <h1>{data?.school || school.toUpperCase()} Records</h1>
        <p className="subtitle">All-time violation reports</p>
        {error && <p role="alert">{error}</p>}
        <div className="summary-card">
          <div><h3>{data ? data.total : "?"}</h3><p>Violation Records</p></div>
          <div>
            <h3>{updatedAt ? updatedAt.toLocaleString("en-PH", { timeZone: "Asia/Manila" }) : "?"}</h3>
            <p>Last Updated (Manila)</p>
          </div>
        </div>
        <div className="recent-card">
          <ViolationTable records={data?.records || []} loading={!data && !error} error={error} />
        </div>
      </div>
    </>
  );
}

export default SchoolRecords;

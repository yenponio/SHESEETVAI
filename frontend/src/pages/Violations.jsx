import Sidebar from "../components/Sidebar";

function Violations() {
  return (
    <>
      <Sidebar />

      <div
        style={{
          marginLeft: "70px",
          padding: "40px",
        }}
      >
        <h1>Dress Code Violations</h1>

        <table border="1" cellPadding="10">
          <thead>
            <tr>
              <th>Date</th>
              <th>Student</th>
              <th>Violation</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td>July 22, 2026</td>
              <td>Juan Dela Cruz</td>
              <td>No ID</td>
              <td>Denied</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

export default Violations;
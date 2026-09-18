export default function ViolationTable({ records, loading, error }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Student No.</th><th>Name</th><th>School</th>
          <th>Violation Type</th><th>Date</th><th>Time (Manila)</th>
        </tr>
      </thead>
      <tbody>
        {records.map(record => (
          <tr key={record.id}>
            <td>{record.studentNumber}</td><td>{record.name}</td>
            <td title={record.collegeName}>{record.college}</td>
            <td>{record.violationType || "Unspecified"}</td>
            <td>{record.date}</td><td>{record.time}</td>
          </tr>
        ))}
        {records.length === 0 && (
          <tr><td colSpan="6">
            {loading ? "Loading violation records..." : error ? "Violation records are unavailable." : "No violation records found."}
          </td></tr>
        )}
      </tbody>
    </table>
  );
}

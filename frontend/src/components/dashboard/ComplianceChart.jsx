import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

const COLORS = ["#2ecc71", "#e74c3c"];

function ComplianceChart({ data = [] }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return (
    <>
      <h2 style={{ marginBottom: "20px", color: "#7b1113" }}>Dress Code Compliance</h2>
      <p>{total} registered students</p>
      <p>Each student is counted once, based on all-time violation records.</p>
      {total === 0 ? <p>No students found.</p> : (
        <ResponsiveContainer width="100%" height={320}>
          <PieChart>
            <Pie data={data} innerRadius={70} outerRadius={110}
              paddingAngle={data.every(item => item.value > 0) ? 4 : 0}
              dataKey="value" label={({ value }) => value > 0 ? value : ""}>
              {data.map((entry, index) => <Cell key={entry.name} fill={COLORS[index]} />)}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </>
  );
}

export default ComplianceChart;

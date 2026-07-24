import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

const data = [
  {
    name: "Compliant",
    value: 184,
  },
  {
    name: "Violation",
    value: 21,
  },
];

const COLORS = [
  "#2ecc71",
  "#e74c3c",
];

function ComplianceChart() {
  return (
    <>
      <h2 style={{ marginBottom: "20px", color: "#7b1113" }}>
        Dress Code Compliance
      </h2>

      <ResponsiveContainer width="100%" height={320}>
        <PieChart>

          <Pie
            data={data}
            innerRadius={70}
            outerRadius={110}
            paddingAngle={4}
            dataKey="value"
            label
          >
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={COLORS[index]}
              />
            ))}
          </Pie>

          <Tooltip />

          <Legend />

        </PieChart>
      </ResponsiveContainer>
    </>
  );
}

export default ComplianceChart;
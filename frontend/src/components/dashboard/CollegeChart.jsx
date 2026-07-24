import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";

const data = [
  { college: "CCJEF", students: 24 },
  { college: "SAS", students: 14 },
  { college: "SBA", students: 17 },
  { college: "SEA", students: 72 },
  { college: "SOC", students: 41 },
  { college: "CHTM", students: 13 },
];

const COLORS = [
  "#3B82F6",
  "#EC4899",
  "#06B6D4",
  "#8B5CF6",
  "#22C55E",
  "#0EA5E9",
];

function CollegeChart() {
  return (
    <>
      <h2 style={{ marginBottom: "20px", color: "#7b1113" }}>
        Students by College
      </h2>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{
            top: 5,
            right: 20,
            left: 10,
            bottom: 5,
          }}
        >

          <XAxis hide />

          <YAxis
            type="category"
            dataKey="college"
          />

          <Tooltip />

          <Bar
              dataKey="students"
              label={{
                  position:"right",
                  fill:"#444",
                  fontWeight:"bold"
              }}
          >
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={COLORS[index]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </>
  );
}

export default CollegeChart;
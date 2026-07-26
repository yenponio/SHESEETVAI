import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";


const COLORS = [
  "#3B82F6",
  "#EC4899",
  "#06B6D4",
  "#8B5CF6",
  "#22C55E",
  "#0EA5E9",
];


function CollegeChart({data}) {

  return (
    <>
      <h2 style={{ marginBottom:"20px", color:"#7b1113" }}>
        Students by College
      </h2>


      <ResponsiveContainer width="100%" height={320}>

        <BarChart
          data={data}
          layout="vertical"
          margin={{
            top:5,
            right:20,
            left:10,
            bottom:5
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

            {
              data.map((item,index)=>(
                <Cell
                  key={index}
                  fill={COLORS[index % COLORS.length]}
                />
              ))
            }

          </Bar>


        </BarChart>

      </ResponsiveContainer>

    </>
  );
}


export default CollegeChart;
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Tooltip,
  Legend,
  Cell,
} from "recharts";
import { useColorScale } from "./utils/useColorScale";

type Props = {
  dataMap: Record<string, number>;
  nameKey?: string; // default "name"
  valueKey?: string; // default "value"
  innerRadius?: number;
  outerRadius?: number;
  height?: number;
};

export default function PieByCategory({
  dataMap,
  nameKey = "name",
  valueKey = "value",
  innerRadius = 40,
  outerRadius = 100,
  height = 300,
}: Props) {
  const entries = Object.entries(dataMap || {});
  const data = entries.map(([k, v]) => ({ [nameKey]: k, [valueKey]: v }));
  const labels = entries.map(([k]) => k);
  const colors = useColorScale(labels);

  if (data.length === 0) {
    return <div className="text-sm text-gray-600">No data.</div>;
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            dataKey={valueKey}
            nameKey={nameKey}
            outerRadius={outerRadius}
            innerRadius={innerRadius}
            paddingAngle={2}
          >
            {data.map((d) => (
              <Cell
                key={String(d[nameKey])}
                fill={colors[String(d[nameKey])]}
              />
            ))}
          </Pie>
          <Tooltip />
          <Legend verticalAlign="bottom" height={24} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

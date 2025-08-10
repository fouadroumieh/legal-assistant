import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell,
} from "recharts";
import { useColorScale } from "./utils/useColorScale";

type Props = {
  dataMap: Record<string, number>;
  xLabel?: string;
  yLabel?: string;
  height?: number;
  showLegend?: boolean;
};

export default function BarByCategory({
  dataMap,
  xLabel = "label",
  yLabel = "value",
  height = 300,
  showLegend = false,
}: Props) {
  const entries = Object.entries(dataMap || {});
  const data = entries.map(([k, v]) => ({ [xLabel]: k, [yLabel]: v }));
  const labels = entries.map(([k]) => k);
  const colors = useColorScale(labels);

  if (data.length === 0) {
    return <div className="text-sm text-gray-600">No data.</div>;
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
        >
          <XAxis dataKey={xLabel} angle={-15} textAnchor="end" height={50} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          {showLegend && <Legend verticalAlign="bottom" height={24} />}
          <Bar dataKey={yLabel} radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell key={String(d[xLabel])} fill={colors[String(d[xLabel])]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

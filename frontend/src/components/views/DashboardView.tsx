import React from "react";
import { apiFetch } from "../../lib/api";
import ChartCard from "../charts/ChartCard";
import BarByCategory from "../charts/BarByCategory";
import PieByCategory from "../charts/PieByCategory";

type DashboardData = {
  ok?: boolean;
  agreement_types?: Record<string, number>;
  jurisdictions?: Record<string, number>;
  industries?: Record<string, number>;
};

export default function DashboardView() {
  const [data, setData] = React.useState<DashboardData | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [err, setErr] = React.useState<string>("");

  async function load() {
    setLoading(true);
    setErr("");
    try {
      const res = await apiFetch("/dashboard");
      setData(res);
    } catch (e: any) {
      setErr(e?.message || "Error loading dashboard");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    load();
  }, []);

  const hasAnyData = Boolean(
    (data?.agreement_types && Object.keys(data.agreement_types).length) ||
      (data?.jurisdictions && Object.keys(data.jurisdictions).length) ||
      (data?.industries && Object.keys(data.industries).length)
  );

  const industries = Object.entries(data?.industries || {}).sort(
    (a, b) => b[1] - a[1]
  );
  const jurisdictions = Object.entries(data?.jurisdictions || {}).sort(
    (a, b) => b[1] - a[1]
  );

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Dashboard</h2>
          <button className="btn" onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
        {err && <div className="mt-2 text-sm text-red-600">{err}</div>}
        {!loading && !err && !hasAnyData && (
          <div className="mt-3 text-sm text-gray-600">No data yet.</div>
        )}
      </div>

      {/* Charts */}
      <div className="grid gap-6 md:grid-cols-2">
        <ChartCard title="Agreements by Type">
          <BarByCategory dataMap={data?.agreement_types || {}} />
        </ChartCard>

        <ChartCard title="Governing Law Breakdown">
          <PieByCategory dataMap={data?.jurisdictions || {}} />
        </ChartCard>
      </div>

      {/* Tables */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card space-y-3">
          <h3 className="text-base font-semibold">Industries</h3>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="th">Industry</th>
                  <th className="th text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {industries.length === 0 && (
                  <tr>
                    <td className="td" colSpan={2}>
                      <span className="text-sm text-gray-600">
                        No industry data.
                      </span>
                    </td>
                  </tr>
                )}
                {industries.map(([name, count]) => (
                  <tr key={name} className="hover:bg-gray-50">
                    <td className="td">{name}</td>
                    <td className="td text-right">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card space-y-3">
          <h3 className="text-base font-semibold">Governing Law</h3>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="th">Jurisdiction</th>
                  <th className="th text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {jurisdictions.length === 0 && (
                  <tr>
                    <td className="td" colSpan={2}>
                      <span className="text-sm text-gray-600">
                        No governing law data.
                      </span>
                    </td>
                  </tr>
                )}
                {jurisdictions.map(([name, count]) => (
                  <tr key={name} className="hover:bg-gray-50">
                    <td className="td">{name}</td>
                    <td className="td text-right">{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

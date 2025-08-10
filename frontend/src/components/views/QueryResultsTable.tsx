// QueryResultsTable.tsx
import React from "react";

type Row = {
  document: string;
  governing_law?: string;
  agreement_type?: string;
  industry?: string;
};

type QueryResultsTableProps = {
  rows: Row[];
  loading?: boolean;
};

export default function QueryResultsTable({
  rows,
  loading,
}: QueryResultsTableProps) {
  const showSkeleton = !!loading;

  // If not loading and no data, render nothing (or your "no results" message in parent)
  if (!showSkeleton && rows.length === 0) return null;

  // Render a small skeleton table while loading
  const skeletonRows = Array.from({ length: 5 });

  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">Results</h2>
        {loading && (
          <span className="inline-flex items-center text-sm text-gray-500">
            <svg
              className="mr-2 h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
                opacity="0.25"
              />
              <path d="M22 12a10 10 0 0 1-10 10" fill="currentColor" />
            </svg>
            Searching…
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th className="th">Document</th>
              <th className="th">Governing Law</th>
              <th className="th">Agreement Type</th>
              <th className="th">Industry</th>
            </tr>
          </thead>

          <tbody>
            {showSkeleton
              ? skeletonRows.map((_, i) => (
                  <tr key={`s-${i}`}>
                    <td className="td">
                      <div className="h-4 w-48 animate-pulse rounded bg-gray-200" />
                    </td>
                    <td className="td">
                      <div className="h-4 w-28 animate-pulse rounded bg-gray-200" />
                    </td>
                    <td className="td">
                      <div className="h-4 w-32 animate-pulse rounded bg-gray-200" />
                    </td>
                    <td className="td">
                      <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
                    </td>
                  </tr>
                ))
              : rows.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="td">{r.document}</td>
                    <td className="td">{r.governing_law}</td>
                    <td className="td">{r.agreement_type}</td>
                    <td className="td">{r.industry}</td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

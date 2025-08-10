import React from "react";

export default function ChartCard({
  title,
  children,
  footer,
  height = 300,
}: {
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  height?: number;
}) {
  return (
    <div className="card">
      <h3 className="text-base font-semibold mb-3">{title}</h3>
      <div style={{ width: "100%", height }}>{children}</div>
      {footer && <div className="mt-2 text-sm text-gray-600">{footer}</div>}
    </div>
  );
}

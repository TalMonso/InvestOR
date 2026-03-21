import { useState } from "react";

interface Props {
  metrics: Record<string, number>;
}

function formatValue(key: string, val: number): string {
  if (key.includes("ratio") || key.includes("kelly") || key.includes("margin") || key.includes("roic") || key.includes("pegy")) {
    return val.toFixed(4);
  }
  if (key.includes("price") || key.includes("eps") || key.includes("value") || key.includes("capex") || key.includes("earnings")) {
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  if (key.includes("shares")) {
    return val.toLocaleString();
  }
  return val.toFixed(4);
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function MetricsPanel({ metrics }: Props) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(metrics);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-sm font-medium text-gray-300 hover:text-gray-100 transition cursor-pointer"
      >
        <span>Raw Metrics ({entries.length})</span>
        <svg
          className={`h-4 w-4 transform transition ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="border-t border-gray-800 px-5 py-3">
          <table className="w-full text-sm">
            <tbody>
              {entries.map(([key, val]) => (
                <tr key={key} className="border-b border-gray-800/50 last:border-0">
                  <td className="py-1.5 text-gray-400">{formatLabel(key)}</td>
                  <td className="py-1.5 text-right font-mono text-gray-200">
                    {formatValue(key, val)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

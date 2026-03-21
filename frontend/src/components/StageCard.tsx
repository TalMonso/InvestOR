interface Metric {
  label: string;
  value: string;
  hint?: string;
}

interface Props {
  title: string;
  subtitle: string;
  passed: boolean;
  metrics: Metric[];
}

export default function StageCard({ title, subtitle, passed, metrics }: Props) {
  return (
    <div
      className={`rounded-xl border p-5 transition ${
        passed
          ? "border-emerald-700/50 bg-emerald-950/30"
          : "border-red-700/50 bg-red-950/30"
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-semibold text-base text-gray-100">{title}</h3>
          <p className="text-xs text-gray-400">{subtitle}</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-bold tracking-wider ${
            passed
              ? "bg-emerald-600/30 text-emerald-300"
              : "bg-red-600/30 text-red-300"
          }`}
        >
          {passed ? "PASS" : "FAIL"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="text-sm">
              <span className="text-gray-500">{m.label}: </span>
              <span className="text-gray-200 font-mono">{m.value}</span>
            </div>
            {m.hint && (
              <p className="text-[11px] leading-tight text-gray-500 mt-0.5">
                {m.hint}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

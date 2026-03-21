import { useState } from "react";
import SearchBar from "./components/SearchBar";
import LoadingSpinner from "./components/LoadingSpinner";
import StageCard from "./components/StageCard";
import MetricsPanel from "./components/MetricsPanel";
import ReportRenderer from "./components/ReportRenderer";
import { analyzeStock, type AnalyzeResponse } from "./services/api";

function pct(n: number): string {
  return `${(n * 100).toFixed(2)}%`;
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await analyzeStock(ticker);
      setData(result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/60 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-5 flex flex-col items-center gap-4">
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight">
              Invest<span className="text-indigo-400">OR</span>
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Ackman &middot; Buffett &middot; Lynch &middot; Soros &middot;
              Graham &middot; Greenblatt &middot; Marks
            </p>
          </div>
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-8 space-y-6">
        {loading && <LoadingSpinner />}

        {error && (
          <div className="rounded-lg border border-red-700/50 bg-red-950/30 px-5 py-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Verdict banner */}
            <div
              className={`rounded-xl px-6 py-4 text-center font-semibold text-lg ${
                data.overall_pass
                  ? "bg-emerald-600/20 text-emerald-300 border border-emerald-700/40"
                  : "bg-red-600/20 text-red-300 border border-red-700/40"
              }`}
            >
              {data.ticker} @ ${data.current_price.toFixed(2)} &mdash;{" "}
              {data.overall_pass ? "PASSED All Stages" : "REJECTED"}
            </div>

            {/* Stage cards */}
            <div className="grid md:grid-cols-2 gap-4">
              <StageCard
                title="Stage 1: Financial Quality"
                subtitle="Ackman's Criteria"
                passed={data.stage1.passed}
                metrics={[
                  ...data.stage1.roic_values.map((v, i) => ({
                    label: `ROIC Y${i}`,
                    value: pct(v),
                    hint: i === 0
                      ? "How efficiently the company generates profit from its capital."
                      : undefined,
                  })),
                  {
                    label: "Debt Ratio",
                    value: data.stage1.debt_ratio.toFixed(4),
                    hint: "Leverage level; lower means lower bankruptcy risk.",
                  },
                ]}
              />
              <StageCard
                title="Stage 2: Intrinsic Value"
                subtitle="Buffett's Engine"
                passed={data.stage2.passed}
                metrics={[
                  { label: "IV/Share", value: `$${data.stage2.iv_per_share.toFixed(2)}` },
                  {
                    label: "Margin of Safety",
                    value: pct(data.stage2.margin_of_safety),
                    hint: "The discount you are getting on the true intrinsic value.",
                  },
                  {
                    label: "Owner Earnings (FCF)",
                    value: `$${data.stage2.owner_earnings.toLocaleString()}`,
                    hint: "True cash generated after maintaining the business.",
                  },
                  { label: "CapEx", value: `$${data.stage2.capex.toLocaleString()}` },
                ]}
              />
              <StageCard
                title="Stage 3: Growth Premium"
                subtitle="Lynch's Calibration"
                passed={data.stage3.passed}
                metrics={[
                  {
                    label: "PEGY",
                    value: data.stage3.pegy.toFixed(4),
                    hint: "Valuation adjusted for growth and dividends (< 1.0 is cheap).",
                  },
                  { label: "Lynch Fair Value", value: `$${data.stage3.lynch_fair_value.toLocaleString()}` },
                ]}
              />
              <StageCard
                title="Stage 4: Risk Sizing"
                subtitle="Kelly / Soros"
                passed={!!data.stage4}
                metrics={
                  data.stage4
                    ? [
                        { label: "Full Kelly", value: pct(data.stage4.full_kelly) },
                        { label: "Half-Kelly", value: pct(data.stage4.half_kelly) },
                        { label: "b Ratio", value: data.stage4.b_ratio.toFixed(4) },
                      ]
                    : [{ label: "Status", value: "Not computed" }]
                }
              />
            </div>

            {/* Supplementary metrics */}
            <div className="rounded-xl border border-indigo-700/50 bg-indigo-950/20 p-5">
              <div className="mb-3">
                <h3 className="font-semibold text-base text-gray-100">
                  Supplementary Analysis
                </h3>
                <p className="text-xs text-gray-400">
                  Graham &middot; Greenblatt &middot; Marks &middot; Reverse DCF
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm">
                    <span className="text-gray-500">Graham Number: </span>
                    <span className="text-gray-200 font-mono">
                      ${data.supplementary.graham_number.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-[11px] leading-tight text-gray-500 mt-0.5">
                    Strict asset and historical earnings valuation (zero growth assumed).
                  </p>
                </div>
                <div>
                  <div className="text-sm">
                    <span className="text-gray-500">Earnings Yield: </span>
                    <span className="text-gray-200 font-mono">
                      {pct(data.supplementary.earnings_yield)}
                    </span>
                  </div>
                  <p className="text-[11px] leading-tight text-gray-500 mt-0.5">
                    Operating return on the total enterprise value.
                  </p>
                </div>
                <div>
                  <div className="text-sm">
                    <span className="text-gray-500">Interest Coverage: </span>
                    <span
                      className={`font-mono ${
                        data.supplementary.interest_coverage < 3
                          ? "text-red-400 font-bold"
                          : "text-gray-200"
                      }`}
                    >
                      {data.supplementary.interest_coverage.toFixed(2)}x
                      {data.supplementary.interest_coverage < 3 ? " ⚠" : ""}
                    </span>
                  </div>
                  <p className="text-[11px] leading-tight text-gray-500 mt-0.5">
                    How many times operating profit can cover debt interest payments.
                  </p>
                </div>
                <div>
                  <div className="text-sm">
                    <span className="text-gray-500">Implied Growth (Rev. DCF): </span>
                    <span className="text-gray-200 font-mono">
                      {data.supplementary.implied_growth_rate >= 0
                        ? pct(data.supplementary.implied_growth_rate)
                        : ">50% (overvalued)"}
                    </span>
                  </div>
                  <p className="text-[11px] leading-tight text-gray-500 mt-0.5">
                    The annual growth rate already priced into the current stock price.
                  </p>
                </div>
              </div>
            </div>

            {/* Raw metrics */}
            <MetricsPanel metrics={data.raw_metrics} />

            {/* LLM Report */}
            <ReportRenderer markdown={data.llm_report} />
          </>
        )}

        {!loading && !error && !data && (
          <div className="text-center text-gray-600 py-24 space-y-2">
            <p className="text-5xl">&#x1F4C8;</p>
            <p className="text-lg">Enter a ticker above to begin analysis</p>
          </div>
        )}
      </main>

      <footer className="border-t border-gray-800 text-center text-xs text-gray-600 py-4">
        InvestOR &mdash; Fundamental analysis pipeline powered by quantitative models
      </footer>
    </div>
  );
}

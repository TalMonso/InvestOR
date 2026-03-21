const API_BASE = "http://localhost:8000/api";

export interface Stage1 {
  roic_values: number[];
  roic_consistent: boolean;
  debt_ratio: number;
  debt_ratio_ok: boolean;
  passed: boolean;
}

export interface Stage2 {
  capex: number;
  owner_earnings: number;
  dcf_intrinsic_value: number;
  iv_per_share: number;
  margin_of_safety: number;
  mos_ok: boolean;
  passed: boolean;
}

export interface Stage3 {
  pegy: number;
  pegy_ok: boolean;
  lynch_fair_value: number;
  passed: boolean;
}

export interface Stage4 {
  b_ratio: number;
  full_kelly: number;
  half_kelly: number;
}

export interface Supplementary {
  graham_number: number;
  earnings_yield: number;
  interest_coverage: number;
  implied_growth_rate: number;
}

export interface AnalyzeResponse {
  ticker: string;
  current_price: number;
  overall_pass: boolean;
  stage1: Stage1;
  stage2: Stage2;
  stage3: Stage3;
  stage4: Stage4 | null;
  supplementary: Supplementary;
  llm_report: string;
  raw_metrics: Record<string, number>;
}

export async function analyzeStock(ticker: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Analysis request failed");
  }

  return res.json();
}

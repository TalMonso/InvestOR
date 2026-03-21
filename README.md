# InvestOR

A full-stack stock analysis application that evaluates any public company through a **7-investor mathematical pipeline** and generates an AI-powered investment report using a local LLM.

Built with **FastAPI** (Python) and **React** (TypeScript / Vite / Tailwind CSS).

---

## What It Does

Enter a stock ticker (e.g. `AAPL`, `NVDA`, `AMD`) and InvestOR will:

1. Fetch live financial data from **Yahoo Finance**
2. Run it through a **4-stage quantitative pipeline** with strict pass/fail criteria
3. Calculate **4 supplementary metrics** from additional investment legends
4. Send everything to a **local Ollama LLM** that writes a detailed investment report

---

## The Pipeline

### Stage 1 — Financial Quality (Bill Ackman)
| Metric | Formula | Pass Condition |
|--------|---------|----------------|
| ROIC | (Net Income - Dividends) / (Equity + Debt - Cash) | > 10% consistently |
| Debt Ratio | Total Liabilities / Total Assets | ≤ 0.25 |

### Stage 2 — Intrinsic Value (Warren Buffett)
| Metric | Formula | Pass Condition |
|--------|---------|----------------|
| Owner Earnings (FCF) | Operating Cash Flow - \|CapEx\| | Must be positive |
| DCF Intrinsic Value | 5-year projection, 10% discount, 2.5% terminal growth | — |
| Margin of Safety | (IV/Share - Price) / IV/Share | ≥ 30% |

If Owner Earnings ≤ 0, the stock immediately fails Stage 2 (no DCF on negative cash flows).

### Stage 3 — Growth Premium (Peter Lynch)
| Metric | Formula | Pass Condition |
|--------|---------|----------------|
| PEGY Ratio | P/E / (Growth Rate + Dividend Yield) | ≤ 1.0 |
| Lynch Fair Value | EPS × Growth Rate (whole number) | — |

### Stage 4 — Risk Sizing (Kelly Criterion / George Soros)
Only computed if Stages 1–3 all pass.

| Metric | Formula |
|--------|---------|
| Risk/Reward (b) | (IV/Share - Price) / (Price × 0.5) |
| Full Kelly | p - (1-p)/b, where p = 0.60 |
| Half-Kelly | K/2, capped at 20% max allocation |

The Half-Kelly halving is grounded in Soros's **Principle of Fallibility** and **Reflexivity** — all models are inherently flawed.

### Supplementary Metrics
| Metric | Investor | Formula |
|--------|----------|---------|
| Graham Number | Benjamin Graham | √(22.5 × EPS × Book Value/Share) |
| Earnings Yield | Joel Greenblatt | EBIT / Enterprise Value |
| Interest Coverage | Howard Marks | EBIT / Interest Expense (⚠ warning if < 3.0) |
| Implied Growth Rate | Reverse DCF | Binary search for growth rate that justifies market price |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, yfinance, Pydantic |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| LLM | Ollama (local) with Mistral 7B |
| Testing | pytest (70 unit tests) |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** — install with `brew install ollama`

---

## Quick Start

### 1. Clone and set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env
```

### 2. Start Ollama (in a separate terminal)

```bash
ollama serve
```

Then pull the model (one-time download, ~4 GB):

```bash
ollama pull mistral
```

### 3. Start the backend (in the backend directory, with venv activated)

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

### 4. Start the frontend (in a separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 5. Run tests

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend (currently only `ollama` is supported) |
| `OLLAMA_MODEL` | `mistral` | Which Ollama model to use |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |

Configure these in `backend/.env`. The `.env.example` file contains safe defaults.

---

## Project Structure

```
InvestOR/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── api/routes.py        # POST /api/analyze endpoint
│   │   ├── models/schemas.py    # Dataclasses and Pydantic models
│   │   ├── analysis/
│   │   │   ├── stage1_ackman.py     # ROIC, Debt Ratio
│   │   │   ├── stage2_buffett.py    # FCF, DCF, Margin of Safety
│   │   │   ├── stage3_lynch.py      # PEGY, Lynch Fair Value
│   │   │   ├── stage4_kelly.py      # Kelly Criterion, Half-Kelly
│   │   │   └── supplementary.py     # Graham, Greenblatt, Marks, Reverse DCF
│   │   └── services/
│   │       ├── data_fetcher.py      # yfinance data extraction
│   │       ├── pipeline.py          # Orchestrates all stages
│   │       └── llm_service.py       # Ollama prompt builder and API client
│   ├── tests/                   # 70 unit tests across all stages
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                     # Your local config (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main dashboard with stage cards
│   │   ├── components/          # SearchBar, StageCard, ReportRenderer, etc.
│   │   └── services/api.ts     # API client and TypeScript interfaces
│   ├── package.json
│   └── index.html
├── .gitignore
└── README.md
```

---

## How It Works

```
User enters ticker → POST /api/analyze → FastAPI backend
  │
  ├─ yfinance: fetch price, financials, cash flow, balance sheet
  │
  ├─ Stage 1 (Ackman):  ROIC consistency + debt ratio
  ├─ Stage 2 (Buffett): FCF → DCF → Margin of Safety
  ├─ Stage 3 (Lynch):   PEGY ratio + fair value
  ├─ Stage 4 (Kelly):   Half-Kelly allocation (only if 1–3 pass)
  ├─ Supplementary:     Graham Number, Earnings Yield, Interest Coverage, Reverse DCF
  │
  └─ Ollama LLM: generates a detailed markdown report
       │
       └─ JSON response → React frontend renders cards + report
```

---

## Disclaimer

This tool is for **educational purposes only**. It is not financial advice. Always do your own research before making investment decisions.

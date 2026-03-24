# ecommerceERP — Autonomous Inventory Management Agent

A LangGraph-powered **Plan → Act → Reflect** agent that analyses internal ERP
inventory data, fetches competitor market intelligence via Tavily, and produces
a structured restock proposal with full auditability.

---

## Setup

> Requires **Python 3.10+**. A `.venv` is created in the project root.

```bash
# 1. Clone / enter the repo
cd ecommerceERP

# 2. Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the package and all dependencies (runtime + dev)
pip install -e ".[dev]"

# 4. Configure secrets
cp .env.example .env
# Open .env and set TAVILY_API_KEY if you want live market research.
# Leave TAVILY_MOCK=true to run fully offline with mock data (recommended first).
```

---

## Running the agent

### Offline / mock mode (no API key needed)

```bash
# Analyse a low-stock SKU — triggers the full Plan→Act→Reflect loop
# including the market-research branch (stock < 20%)
TAVILY_MOCK=true ecommerce-erp --sku SKU-001

# Analyse a healthy-stock SKU — skips market research
TAVILY_MOCK=true ecommerce-erp --sku SKU-003
```

### Live Tavily mode (requires `TAVILY_API_KEY` in `.env`)

```bash
# .env must contain: TAVILY_API_KEY=tvly-...  and  TAVILY_MOCK=false
source .venv/bin/activate
ecommerce-erp --sku SKU-004
```

### Available mock SKUs

| SKU     | Product                       | Stock % | Triggers market research? |
| ------- | ----------------------------- | ------- | ------------------------- |
| SKU-001 | Wireless Bluetooth Headphones | 7.5%    | ✅ yes                    |
| SKU-002 | USB-C Charging Cable (2m)     | 20.0%   | ❌ no (boundary)          |
| SKU-003 | Ergonomic Office Chair        | 80.0%   | ❌ no                     |
| SKU-004 | Mechanical Keyboard           | 10.0%   | ✅ yes                    |
| SKU-005 | Smart Home Hub                | 35.0%   | ❌ no                     |

### Output

The agent prints:

1. A **human-readable Markdown proposal** showing the Safety Stock calculation table and market adjustment.
2. A **machine-readable JSON proposal** with every field needed for downstream automation.
3. A `⚠️ ACTION REQUIRED: Awaiting Human Approval` pause message before any order is "placed".

The full **reasoning trace** is written as JSONL to `logs/reasoning_trace.log`.
Each line contains `timestamp`, `phase` (PLAN / ACT / REFLECT), `thought`, `action`, and `observation`.

```bash
# Tail the live trace while the agent runs (open a second terminal)
tail -f logs/reasoning_trace.log | python -m json.tool
```

---

## Running the Streamlit demo (Phase 1)

This phase is intentionally public-facing and does not include authentication.

```bash
# Make sure dependencies are installed
source .venv/bin/activate
pip install -e ".[dev]"

# Launch the Streamlit UI
TAVILY_MOCK=true python -m streamlit run src/ecommerce_erp/ui/app.py
```

Open the local URL shown by Streamlit (usually http://localhost:8501).

### Demo workflow

1. Select a SKU in the sidebar.
2. Toggle mock mode on/off.
3. Click Run analysis.
4. Observe live PLAN → ACT → REFLECT trace updates.
5. Review output in Markdown and JSON tabs.
6. Use Approve or Reject to simulate human-in-the-loop decisioning.

---

## Deploy to Streamlit Community Cloud (now)

Use this for immediate public demo hosting.

### 1. Push code to GitHub

Ensure these files are in your repository:

- `streamlit_app.py`
- `requirements.txt`
- `runtime.txt`

### 2. Create the app in Streamlit Cloud

1. Open Streamlit Community Cloud and click **New app**.
2. Select your GitHub repo and branch.
3. Set **Main file path** to `streamlit_app.py`.
4. Click **Deploy**.

### 3. Configure app secrets (recommended)

In app settings, open **Secrets** and add one of these options:

```toml
# Option A: demo-safe mock mode (no API key needed)
TAVILY_MOCK = "true"
```

```toml
# Option B: live market research
TAVILY_MOCK = "false"
TAVILY_API_KEY = "your_real_key"
```

Do not commit `.env` or real API keys to git.

### 4. Verify after deployment

1. Open the hosted app URL.
2. Run `SKU-001` in mock mode.
3. Confirm you see:
  - live PLAN → ACT → REFLECT steps,
  - Markdown and JSON proposal tabs,
  - approval buttons and status update.

### Troubleshooting

- If import errors occur, confirm **Main file path** is exactly `streamlit_app.py`.
- If market calls fail in live mode, verify `TAVILY_API_KEY` in Secrets.
- If app appears stale, use **Reboot app** from Streamlit settings.

---

## Productization roadmap

### Phase 1 (current): Public Streamlit demo

- Completed: interactive UI + live reasoning trace + dual output + approval simulation.

### Phase 2: Service/API layer + auth

- Add FastAPI backend.
- Add authentication: basic auth (internal) and OAuth (external/public).
- Move approval actions to API endpoints.

### Phase 3: Persistence + audit

- Add run/proposal persistence (SQLite first, Postgres later).
- Add immutable audit trail for approval decisions.

### Phase 4: Dockerization

- Add production Dockerfile(s) and docker-compose.
- Add health checks, env-based config, non-root runtime user.

### Phase 5: Enterprise deployment (AWS-first)

- Preferred path for popularity and speed:
  - Containers on ECS Fargate or App Runner.
  - ALB + ACM + Route53 for HTTPS and DNS.
  - Secrets Manager for API keys.
  - CloudWatch for logs/metrics/alarms.

- Azure remains a strong option when your stack is Microsoft-first or needs
  tighter Entra ID integration, but AWS is the practical default for broad
  ecosystem familiarity.

---

## Running the tests

```bash
# Run the full suite (44 tests, all offline — no API key required)
pytest

# With coverage report
pytest --cov=ecommerce_erp --cov-report=term-missing

# Run a specific test module
pytest tests/test_orchestrator.py -v
pytest tests/test_recommendation_engine.py -v
pytest tests/test_guardrails.py -v
pytest tests/test_tools.py -v
```

All tests enforce `TAVILY_MOCK=true` automatically via `tests/conftest.py`, so
no live API calls are ever made during `pytest`.

### What the tests cover

| File                            | What is tested                                                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `test_orchestrator.py`          | Full Plan→Act→Reflect loop, low/healthy/boundary stock branches, cost-guard integration, JSONL trace format |
| `test_recommendation_engine.py` | Safety Stock math (exact values), market adjustment factors, dual JSON+Markdown output                      |
| `test_guardrails.py`            | Cost-guard limits, custom env override, error message content                                               |
| `test_tools.py`                 | Inventory mock data, case-insensitive SKU lookup, Tavily mock/live switching, missing API key handling      |
| `test_smoke.py`                 | Full CLI entry point (`main()`) returns exit code 0                                                         |

---

## Environment variables

| Variable                   | Default  | Description                                              |
| -------------------------- | -------- | -------------------------------------------------------- |
| `TAVILY_API_KEY`           | —        | Required for live market research. Get one at tavily.com |
| `TAVILY_MOCK`              | `false`  | Set `true` for fully offline mock mode                   |
| `MAX_TOOL_CALLS_PER_CYCLE` | `5`      | Cost-guard cap — halts the loop if exceeded              |
| `LOG_DIR`                  | `./logs` | Directory where `reasoning_trace.log` is written         |

---

# The Project

## Agentic ERP Integration & Restock Optimization

### The Concept

A multi-agent system where:

- One agent analyzes sales data (from a mock ERP)
- Another researches market trends
- A third generates a restock strategy.

**Technical Twist:** Use a framework like CrewAI or LangGraph to manage complex state and "agentic" workflows.

---

## The Problem

Inventory management in large-scale e-commerce is often reactive. Human managers spend hours correlating internal sales velocity with external market trends to decide on restock orders.

---

## The Solution

An autonomous multi-agent system that "thinks" through inventory challenges by accessing internal databases and external market APIs.

---

## Key Features

- **Agentic Orchestration:** Uses a state-machine approach (LangGraph) to manage complex, multi-step tasks.
- **Functional Tool-Calling:** The agent is empowered to call Python functions to query ERP systems (Netsuite/Spanner) and search the web for competitor pricing.
- **Context-Aware Reasoning:** The agent doesn't just suggest a number; it provides a "Reasoning Trace" explaining why it suggested a specific restock amount based on lead times and sales trends.
- **Human-in-the-Loop:** Generates a draft proposal that requires human approval via a UI/Slack integration before any orders are "placed."

---

## Tech Stack

- **Framework:** LangGraph
- **UI:** Streamlit
- **Search Tool:** Tavily / Perplexity API
- **Database:** Simulated Spanner/SQL via Python Tooling

---

### System Design Diagram

```mermaid
graph TD
%% Define Nodes and Styles
classDef llm fill:#f9f,stroke:#333,stroke-width:2px;
classDef tool fill:#bbf,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5;
classDef state fill:#dfd,stroke:#333,stroke-width:1px;

    User[User / System Trigger] -->|SKU Request| Orchestrator

    %% The Agent Loop (Orchestrator)
    subgraph "Autonomous Agent Loop (MAPE-K Pattern)"
        Orchestrator(LLM Orchestrator<br/>'Reasoning Brain')
        Plan[1. Generate Plan<br/>Sub-tasks]
        Execute[2. Execute Action<br/>Tool Call]
        Reflect[3. Reflect & Update<br/>Observation]

        Orchestrator --> Plan
        Plan --> Execute
        Execute --> Reflect
        Reflect -->|Is Goal Met?| Orchestrator

        Orchestrator:::llm
    end

    %% The State/Memory Layer
    Reflect -->|Write Trace| StateDB[(Structured State<br/>'Memory' / Logs)]
    Orchestrator -->|Read Context| StateDB
    StateDB:::state

    %% The Tool Execution Layer
    subgraph "Tool Execution Layer"
        ERPTool[Internal Tool:<br/>ERP/Inventory API]
        MarketTool[External Tool:<br/>Tavily Search API]
    end

    Execute -->|Call| ERPTool
    Execute -->|Call| MarketTool

    ERPTool -->|Mock Stock Data| Reflect
    MarketTool -->|Competitor Prices| Reflect
    ERPTool:::tool
    MarketTool:::tool

    %% Final Output
    Orchestrator -->|Final Goal Achieved| Proposal[Generate Structured<br/>Restock Proposal]
```

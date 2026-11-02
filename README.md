# PROCUREMENTIQ AI — Autonomous Procurement Risk & Negotiation Intelligence

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Autonomous%20Agents-FF6F00?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash%20%2F%202.0-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![ReportLab](https://img.shields.io/badge/ReportLab-Vector%20PDF-007ACC?style=for-the-badge)](https://www.reportlab.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br/>

> **An autonomous procurement intelligence platform with six specialized agents powered by LangGraph and Gemini to analyze supplier quotations, evaluate supply chain risks, optimize total costs, and generate strategic negotiation recommendations.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Capabilities](#-key-capabilities)
- [6-Agent AI Architecture](#-6-agent-ai-architecture)
- [Vendor Scoring Engine & Formulas](#-vendor-scoring-engine--formulas)
- [Pastel Enterprise Design System](#-pastel-enterprise-design-system)
- [Dual Execution Modes (LLM & Offline Demo)](#-dual-execution-modes)
- [Quickstart Guide](#-quickstart-guide)
- [Demo Credentials](#-demo-credentials)
- [Automated Test Suite](#-automated-test-suite)
- [Project Directory Structure](#-project-directory-structure)
- [Security & Data Governance](#-security--data-governance)
- [License](#-license)

---

## 🔭 Overview

**PROCUREMENTIQ AI** is an enterprise-grade, autonomous procurement intelligence web application engineered to ingest supplier quotations (PDF, XLSX, CSV), evaluate multifaceted supply chain risks, calculate transparent landed total cost of ownership (TCO), and generate explainable vendor rankings through a deterministic 6-agent AI architecture.

The platform bridges enterprise ERP needs and autonomous AI workflows by delivering strict mathematical accuracy for commercial calculations while leveraging **Google Gemini** and **LangGraph** for qualitative risk synthesis, counter-offer strategies, and negotiation playbooks.

---

## 🌟 Key Capabilities

1. **Multi-Format Quotation Extraction**
   - Ingests multi-page PDFs, Excel spreadsheets (`.xlsx`), and `.csv` files using PyMuPDF and openpyxl.
   - Interactive user review interface for side-by-side field reconciliation and line-item corrections.

2. **Deterministic 6-Agent Architecture**
   - **Agent 1: Requirement Parser Agent** — Extracts constraints (budget ceiling, delivery deadline, warranty minimum) and commercial preferences.
   - **Agent 2: Quote Analyzer Agent** — Normalizes quotation line items, discounts, shipping, taxes, and flags missing or unverified fields.
   - **Agent 3: Supplier Researcher Agent** — Surfaces historical performance, certified factory audits, reliability metrics, and information gaps.
   - **Agent 4: Risk Assessor Agent** — Multi-factor risk evaluation across lead times, warranty deficit, payment terms, and single-source dependency.
   - **Agent 5: Cost Optimizer Agent** — Deterministic landed cost calculation with itemized charge breakdowns and budget variance analysis.
   - **Agent 6: Procurement Advisor Agent** — Configurable 4-pillar vendor scoring, hard constraint gating, trade-off analysis, and counter-offer negotiation playbooks.

3. **Transparent & Explainable Scoring Engine**
   - Total Cost: 40% (relative landed cost normalization)
   - Delivery Performance: 25% (lead time vs. requirement deadline)
   - Risk Assessment: 20% (heuristic risk penalty scale)
   - Warranty & Support: 15% (coverage duration vs. requirement minimum)
   - **Constraint Gating**: Over-budget, late-delivery, or sub-warranty vendors are explicitly disqualified and flagged.

4. **Dual Execution Engine (LLM Mode & Offline DEMO MODE)**
   - Operates 100% out-of-the-box in **DEMO MODE** with zero external API keys required.
   - Supports plug-and-play cloud LLM providers (**Google Gemini**, **Groq**, **OpenAI**) configured via environment variables or UI settings.

5. **Executive Reporting & Export**
   - Full vector PDF export generated natively via ReportLab with branding, KPI cards, itemized cost comparison tables, and audit logs.
   - RFC 4180 CSV export for direct ERP/procurement spreadsheet integration.

---

## 🤖 6-Agent AI Architecture

```
                       ┌────────────────────────┐
                       │  Procurement Request   │
                       └───────────┬────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 1: Requirement Parser (LangGraph / Gemini) │
          │ Extracts Budget Cap, Delivery Target, Warranty   │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 2: Quote Analyzer (PyMuPDF / openpyxl)     │
          │ Normalizes Quotes, Line Items, Flags Gaps        │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 3: Supplier Researcher                     │
          │ Queries Historical Audits, ESG & Reliability     │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 4: Risk Assessor                           │
          │ Evaluates Lead Time, Warranty & Single-Source    │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 5: Cost Optimizer                          │
          │ Calculates Landed TCO, Tax/Freight, Variances    │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │ Agent 6: Procurement Advisor                     │
          │ 4-Pillar Scoring, Constraint Gating & Playbooks  │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
             ┌───────────────────────────────────────────┐
             │ Ranked Vendor Shortlist & Negotiation Deck│
             └───────────────────────────────────────────┘
```

---

## 📐 Vendor Scoring Engine & Formulas

### Landed Total Cost of Ownership (TCO)
$$\text{Subtotal} = \text{Unit Price} \times \text{Quantity}$$
$$\text{Net Subtotal} = \text{Subtotal} - \text{Applicable Discount}$$
$$\text{Total Landed Cost} = \text{Net Subtotal} + \text{Taxes} + \text{Shipping} + \text{Installation} + \text{Other Surcharges}$$

### 4-Pillar Weighted Score Formula
$$\text{Overall Score} = (S_{\text{Cost}} \times 0.40) + (S_{\text{Delivery}} \times 0.25) + (S_{\text{Risk}} \times 0.20) + (S_{\text{Warranty}} \times 0.15)$$

- **Cost Score ($S_{\text{Cost}}$)**: Relative landed cost normalized against lowest compliant bid.
- **Delivery Score ($S_{\text{Delivery}}$)**: Measured delivery timeline against target operational deadline.
- **Risk Score ($S_{\text{Risk}}$)**: Penalty assessment across supplier financial stability, audit certification, and dispute history.
- **Warranty Score ($S_{\text{Warranty}}$)**: Coverage duration and SLA compliance against specified baseline.

---

## 🎨 Pastel Enterprise Design System

Built strictly adhering to the **Pastel Enterprise Design System**, featuring:
- **Palette Tokens**: Pastel Blue (`#E5F0FF`), Lavender (`#F0E9FF`), Peach (`#FFF0E7`), Mint (`#E1F8EF`), Navy (`#172554`).
- **Cards & Elevation**: Soft 16–22px rounded radius, gentle drop shadows, and subtle borders.
- **Zero Frontend Build Dependencies**: Pure HTML5, CSS3, vanilla JavaScript, Chart.js, and Bootstrap Icons served via CDN.

---

## ⚡ Dual Execution Modes

| Feature | Offline DEMO MODE (Default) | Cloud LLM Mode |
|---|---|---|
| **API Keys Needed** | None (0 external dependencies) | Google Gemini, Groq, or OpenAI key |
| **Agent Execution** | Deterministic rule-based engine | LangGraph orchestrating LLM calls |
| **Mathematical Accuracy** | 100% deterministic | 100% deterministic (LLM does not compute math) |
| **Negotiation Playbooks** | Rule-derived strategic tips | Contextual LLM counter-offer synthesis |
| **Graph Generation** | Pre-computed analytical metrics | Dynamic visual breakdown via Gemini |

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/JestuAshok/PROCUREMENTIQ-AI---Python-Flask-LangGraph-SQLite---Google-Gemini.git
cd PROCUREMENTIQ-AI---Python-Flask-LangGraph-SQLite---Google-Gemini
```

### 2. Set Up a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```
*(Default settings enable full offline **DEMO MODE** immediately with zero API keys required.)*

### 5. Launch Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
The application will automatically initialize the SQLite database (`instance/procurementiq.db`) and seed realistic supplier profiles and mock requests on first run.

---

## 🔑 Demo Credentials

A pre-configured procurement manager account is available out of the box:
- **Email:** `jahnavi@procurementiq.ai`
- **Password:** `Password123!`

*(You can also register a brand-new account on `/signup` with instant SQLite persistence and secure PBKDF2 password hashing.)*

---

## 🧪 Automated Test Suite

An automated end-to-end acceptance test suite validates all core system components:
```bash
python tests/test_app.py
```

### Validated Test Cases:
- [x] Application startup and environment integrity
- [x] Public landing page and navigation route resolution
- [x] Password hashing and SQLite authentication
- [x] Session persistence and route authorization gating
- [x] Unique procurement request generation (`PR-2026-XXX`)
- [x] Multi-format quotation parsing (PDF, XLSX, CSV)
- [x] 6-Agent sequential execution via LangGraph / deterministic fallback
- [x] Landed cost calculations (Subtotal, Discounts, Freight, Taxes)
- [x] Scoring engine constraint gating and disqualification flags
- [x] Missing field disclosure and audit warnings
- [x] Dynamic database-derived KPI aggregations
- [x] Vector PDF and RFC 4180 CSV export generation
- [x] Database persistence across service restarts
- [x] Offline DEMO MODE verification with 0 API keys

---

## 📁 Project Directory Structure

```
PROCUREMENTIQ-AI/
├── app.py                     # Flask application entry point
├── config.py                  # App configuration & default scoring weights
├── requirements.txt           # Python package requirements
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules (protects .env and databases)
├── README.md                  # Comprehensive documentation
├── database/
│   ├── db.py                  # SQLite helper functions & query connection pools
│   ├── schema.sql             # Relational schema (13 tables, foreign keys, indexes)
│   └── seed.py                # Reference data seeder
├── agents/
│   ├── requirement_parser.py  # Agent 1: Request constraint parser
│   ├── quote_analyzer.py      # Agent 2: Quotation line-item normalizer
│   ├── supplier_researcher.py # Agent 3: Historical audits & vendor intelligence
│   ├── risk_assessor.py       # Agent 4: Multi-factor risk engine
│   ├── cost_optimizer.py      # Agent 5: Net landed TCO & budget variance
│   ├── procurement_advisor.py # Agent 6: Shortlist & counter-offer playbooks
│   └── workflow.py            # LangGraph pipeline orchestrator
├── services/
│   ├── cost_calculator.py     # Deterministic landed cost calculator
│   ├── scoring_engine.py      # Multi-criteria scoring & constraint gating
│   ├── quotation_extractor.py # Document parser (PyMuPDF / openpyxl / CSV)
│   ├── gemini_service.py      # Google Gemini LLM synthesis service
│   ├── sample_data_service.py # Realistic quotation document generator
│   └── report_service.py      # ReportLab executive PDF & CSV generator
├── routes/
│   ├── auth.py                # User login, registration, session management
│   ├── dashboard.py           # Executive dashboard & live KPIs
│   ├── procurement.py         # Request creation & file uploads
│   ├── analysis.py            # Quotation review & reconciliation
│   ├── suppliers.py           # Supplier directory & audit records
│   ├── risks.py               # Risk matrix & category breakdown
│   ├── costs.py               # Landed cost comparisons & breakdowns
│   ├── recommendations.py     # Ranked supplier cards & human override modal
│   ├── workflow_routes.py     # 6-Agent workflow execution & logs
│   ├── reports.py             # PDF & CSV report generation
│   └── settings.py            # Custom weights & LLM API keys
├── templates/                 # Jinja2 HTML templates (Pastel UI System)
├── static/
│   ├── css/                   # Stylesheets (tokens, dashboard, auth)
│   ├── js/                    # Client-side scripts (modals, charts, dropzones)
│   └── images/                # Visual assets and illustrations
├── sample_documents/          # Auto-generated sample quotation documents
└── tests/
    └── test_app.py            # Functional acceptance test suite
```

---

## 🔒 Security & Data Governance

- **Password Hashing:** Passwords hashed with PBKDF2:SHA256 via `werkzeug.security`.
- **Environment Isolation:** Sensitive API keys stored only in local `.env` (strictly ignored by `.gitignore`).
- **File Validation:** Strict extension checking (`.pdf`, `.xlsx`, `.csv`), file size limits (16 MB), and `secure_filename` sanitization.
- **SQL Injection Prevention:** 100% parameterized queries via SQLite parameter bindings.
- **XSS Protection:** Automatic template HTML escaping enabled across all Jinja2 templates.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

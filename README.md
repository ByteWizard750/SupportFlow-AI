# SupportFlow AI

**SupportFlow AI** is an AI-Powered Support Ticket Intelligence and Response Assistant built with Python, Streamlit, SQLite, Google Gemini, Sentence Transformers, and FAISS.

---

## Development Status

- [x] **Phase 1: Application Foundation** (SQLite persistence, multi-page UI, ticket submission, ticket queue)
- [x] **Phase 2: AI Ticket Analysis** (Gemini structured metadata classification: Category, Priority, Sentiment, Department, Reasoning)
- [x] **Phase 3: RAG Knowledge Base & Suggested Response** (Local embeddings, FAISS vector search, grounded response generation, deterministic source attribution)
- [x] **Phase 4: AI Analytics & Support Intelligence Dashboard** (SQL-based real-time KPIs, 2x2 AI distribution charts, workload allocation, urgent escalation queue, on-demand Gemini executive briefing)
- [x] **Phase 5: Human-in-the-Loop Workflow** (Agent review panel, draft editing, status transitions: New → AI Analyzed → In Progress → Resolved, resolution tracking, lifecycle KPIs)

---

## Knowledge Base Documentation (Demo Data)

> **Notice**: The policy and FAQ documents included in `knowledge_base/` are sample mock documents created specifically for demonstration and evaluation purposes of this prototype:
> - `knowledge_base/refund_policy.txt`: Sample 14-day refund window, renewal refund rules, processing timelines.
> - `knowledge_base/billing_policy.txt`: Accepted payment methods, billing frequencies, failed payment retry logic.
> - `knowledge_base/account_faq.txt`: Password resets, 30-min session timeout, 2FA procedures, account lockout thresholds.
> - `knowledge_base/subscription_policy.txt`: Starter ($29), Professional ($99), Enterprise tiers, upgrade/downgrade rules.
> - `knowledge_base/technical_faq.txt`: 25MB file upload limit, supported browsers, API rate quotas, 500 error reporting.

---

## Project Structure

```text
SupportFlow-AI/
├── knowledge_base/               # Sample internal company documentation
│   ├── refund_policy.txt
│   ├── billing_policy.txt
│   ├── account_faq.txt
│   ├── subscription_policy.txt
│   └── technical_faq.txt
├── vector_store/                 # Auto-generated FAISS vector index & metadata
│   ├── faiss_index.bin
│   └── chunks_metadata.json
├── database/
│   ├── __init__.py
│   └── database.py               # SQLite schema (tickets, ticket_analyses, ticket_rag_responses, ticket_resolutions)
├── services/
│   ├── __init__.py
│   ├── ticket_service.py         # Business operations & workflow orchestration
│   ├── ai_service.py             # Gemini ticket classification & prompt engineering
│   ├── rag_service.py            # Local SentenceTransformers + FAISS semantic search
│   ├── response_service.py       # Grounded response drafting & source attribution
│   ├── analytics_service.py      # Dashboard analytics formatting & on-demand Gemini executive brief
│   └── agent_service.py          # Human-in-the-loop draft editing & ticket resolution workflow
├── pages/
│   ├── dashboard.py              # Support Intelligence Dashboard (Lifecycle KPIs, Charts, Tables, AI Brief)
│   ├── new_ticket.py             # Balanced centered ticket creation form
│   └── tickets.py                # Ticket Queue, AI Inspector, and Agent Review & Resolution panel
├── app.py                        # Main Streamlit application entry point
├── config.py                     # Secure environment and Gemini API key manager
├── requirements.txt              # Project dependencies
├── test_phase1.py                # Foundation unit tests (5 tests)
├── test_phase2.py                # AI analysis unit tests (4 tests)
├── test_phase3.py                # RAG & retrieval unit tests (6 tests)
├── test_phase4.py                # Analytics & aggregation unit tests (5 tests)
├── test_phase5.py                # Human-in-the-loop workflow unit tests (7 tests)
└── README.md
```

---

## Complete Support Lifecycle: Phase 1 to Phase 5

```text
Customer Ingestion
       ↓
[ Create Ticket ] (SQLite: status='New')
       ↓
[ AI Triage Intelligence ] (Gemini classification: Category, Priority, Sentiment, Department -> status='AI Analyzed')
       ↓
[ Grounded RAG Retrieval ] (Local FAISS semantic search -> internal company policy context)
       ↓
[ AI Suggested Response ] (Grounded draft + deterministic source citations)
       ↓
[ Agent Review & Edit ] (Human support agent modifies draft response -> status='In Progress')
       ↓
[ Ticket Resolution ] (Agent approves final customer response -> status='Resolved', timestamped in SQLite)
       ↓
[ Support Intelligence ] (SQL real-time lifecycle KPIs, 2x2 distribution charts, Recent Resolutions, Executive AI Brief)
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Google Gemini API Key

### 2. Setup Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key
Create or edit your local `.env` file (protected from git):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 4. Run the Application

```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## Running Automated Tests

```bash
# Run complete test suite across all 5 phases (27 unit tests, zero API quota consumed)
.venv/bin/python test_phase1.py
.venv/bin/python test_phase2.py
.venv/bin/python test_phase3.py
.venv/bin/python test_phase4.py
.venv/bin/python test_phase5.py

# Optional: Run live Gemini API integration tests
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase2.py
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase3.py
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase4.py
```

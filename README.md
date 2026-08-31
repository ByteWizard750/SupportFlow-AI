# SupportFlow AI

**SupportFlow AI** is an AI-Powered Support Ticket Intelligence and Response Assistant built with Python, Streamlit, SQLite, Google Gemini, Sentence Transformers, and FAISS.

---

## Development Status

- [x] **Phase 1: Application Foundation** (SQLite persistence, multi-page UI, ticket submission, ticket queue)
- [x] **Phase 2: AI Ticket Analysis** (Gemini structured metadata classification: Category, Priority, Sentiment, Department, Reasoning)
- [x] **Phase 3: RAG Knowledge Base & Suggested Response** (Local embeddings, FAISS vector search, grounded response generation, deterministic source attribution)
- [x] **Phase 4: AI Analytics & Support Intelligence Dashboard** (SQL-based real-time KPIs, 2x2 AI distribution charts, workload allocation, urgent escalation queue, on-demand Gemini executive briefing)
- [ ] **Phase 5: Human-in-the-Loop Workflow** (Agent review, editing, approval/rejection, resolution states)

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
│   └── database.py               # SQLite schema & SQL analytics aggregations
├── services/
│   ├── __init__.py
│   ├── ticket_service.py         # Business operations & workflow orchestration
│   ├── ai_service.py             # Gemini ticket classification & prompt engineering
│   ├── rag_service.py            # Local SentenceTransformers + FAISS semantic search
│   ├── response_service.py       # Grounded response drafting & source attribution
│   └── analytics_service.py      # Dashboard analytics formatting & on-demand Gemini executive brief
├── pages/
│   ├── dashboard.py              # Support Intelligence Dashboard (KPIs, Charts, Urgent Queue, AI Brief)
│   ├── new_ticket.py             # Balanced centered ticket creation form
│   └── tickets.py                # Full-width stacked ticket queue & AI resolution inspector
├── app.py                        # Main Streamlit application entry point
├── config.py                     # Secure environment and Gemini API key manager
├── requirements.txt              # Project dependencies
├── test_phase1.py                # Foundation unit tests (5 tests)
├── test_phase2.py                # AI analysis unit tests (4 tests)
├── test_phase3.py                # RAG & retrieval unit tests (6 tests)
├── test_phase4.py                # Analytics & aggregation unit tests (5 tests)
└── README.md
```

---

## Phase 4 Architecture: Support Intelligence Dashboard

1. **Quota-Safe SQL-Powered Analytics**:
   - All top KPI metric cards, distribution charts, and workload tables run on local SQLite `GROUP BY` and `JOIN` aggregations with **< 2ms execution time** and **zero API quota consumed**.
2. **2 x 2 AI Intelligence Chart Grid**:
   - **Category Distribution**: Horizontal bar chart for long category labels.
   - **Department Workload**: Column chart comparing support team routing.
   - **Priority Spectrum**: Color-coded severity distribution (Critical, High, Medium, Low).
   - **Customer Sentiment Pulse**: Emotional sentiment breakdown (Positive, Neutral, Negative, Frustrated).
3. **Urgent Escalation Queue**:
   - Dedicated table highlighting High and Critical priority tickets for immediate support action.
4. **On-Demand Executive AI Brief**:
   - A dedicated card powered by Google Gemini (`gemini-3-flash-preview`) that synthesizes current support trends into exactly 3 structured insights:
     1. Primary Customer Pain Point
     2. Highest Workload / Risk Area
     3. Recommended Operational Action
   - **Strictly on-demand**: Only runs when the user clicks "Generate Executive AI Brief", with results cached in `st.session_state` to conserve API quota.

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
# Run complete test suite (20 automated unit tests, zero API quota consumed)
.venv/bin/python test_phase1.py
.venv/bin/python test_phase2.py
.venv/bin/python test_phase3.py
.venv/bin/python test_phase4.py

# Optional: Run live Gemini API integration tests
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase2.py
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase3.py
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase4.py
```

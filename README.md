# SupportFlow AI

**SupportFlow AI** is an AI-Powered Support Ticket Intelligence and Response Assistant built with Python, Streamlit, SQLite, Google Gemini, Sentence Transformers, and FAISS.

---

## Development Status

- [x] **Phase 1: Application Foundation** (SQLite persistence, multi-page UI, ticket submission, ticket queue)
- [x] **Phase 2: AI Ticket Analysis** (Gemini structured metadata classification: Category, Priority, Sentiment, Department, Reasoning)
- [x] **Phase 3: RAG Knowledge Base & Suggested Response** (Local embeddings, FAISS vector search, grounded response generation)
- [ ] **Phase 4: AI Response Generation Refinements**
- [ ] **Phase 5: Human-in-the-Loop Workflow** (Review, editing, approval/rejection, resolution states)
- [ ] **Phase 6: Dashboard & Final Improvements**

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
│   └── database.py               # SQLite schema (tickets, ticket_analyses, ticket_rag_responses)
├── services/
│   ├── __init__.py
│   ├── ticket_service.py         # Business operations & workflow orchestration
│   ├── ai_service.py             # Gemini ticket classification & prompt engineering
│   ├── rag_service.py            # Local SentenceTransformers + FAISS semantic search
│   └── response_service.py       # Grounded response drafting & deterministic source attribution
├── pages/
│   ├── dashboard.py              # Operational metrics and recent ticket table
│   ├── new_ticket.py             # Ticket creation form
│   └── tickets.py                # Ticket queue, AI Intelligence & Suggested Response
├── app.py                        # Main Streamlit application entry point
├── config.py                     # Secure environment and Gemini API key manager
├── requirements.txt              # Project dependencies
├── test_phase1.py                # Foundation unit tests
├── test_phase2.py                # AI analysis unit tests
├── test_phase3.py                # RAG & retrieval unit tests
└── README.md
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
# Run unit test suites (uses isolated temporary databases, zero API quota consumed)
.venv/bin/python test_phase1.py
.venv/bin/python test_phase2.py
.venv/bin/python test_phase3.py

# Optional: Run live Gemini API integration tests
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase2.py
RUN_LIVE_GEMINI=1 .venv/bin/python test_phase3.py
```

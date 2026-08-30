# SupportFlow AI

**SupportFlow AI** is an AI-Powered Support Ticket Intelligence and Response Assistant built with Python, Streamlit, SQLite, and (in future phases) LLMs and RAG.

---

## Current Status: Phase 1 — Application Foundation

Phase 1 establishes the core application architecture, database persistence layer, service abstraction, and multi-page Streamlit workspace.

### Features in Phase 1
- **Database Layer**: SQLite database (`supportflow.db`) with `tickets` table storing `id`, `customer_name`, `subject`, `description`, `status`, and `created_at`.
- **Service Layer**: Input validation and business logic separating UI from persistence.
- **Dashboard**: Real-time database metrics (**Total Tickets**, **New Tickets**) and recent tickets queue.
- **New Ticket Submission**: Form with client validation, database insertion, and automated status initialization to `New`.
- **Ticket Queue & Detail Inspector**: Searchable/filterable ticket list with detailed ticket view.

---

## Project Structure

```text
SupportFlow-AI/
├── database/
│   ├── __init__.py
│   └── database.py          # SQLite connection and CRUD operations
├── services/
│   ├── __init__.py
│   └── ticket_service.py    # Validation and business logic
├── pages/
│   ├── dashboard.py         # Metrics & recent tickets
│   ├── new_ticket.py        # Ticket submission form
│   └── tickets.py           # Ticket queue and details view
├── app.py                   # Main Streamlit application entry point
├── requirements.txt         # Dependencies
├── README.md                # Documentation
└── PROJECT_BLUEPRINT.md     # Architecture & roadmap specification
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)

### 2. Setup Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

Open your browser and navigate to `http://localhost:8501`.

---

## Development Roadmap
- **Phase 1: Application Foundation** (Completed)
- **Phase 2: AI Ticket Analysis** (Upcoming)
- **Phase 3: RAG Knowledge Base** (Upcoming)
- **Phase 4: AI Response Generation** (Upcoming)
- **Phase 5: Human-in-the-Loop Workflow** (Upcoming)
- **Phase 6: Dashboard & Final Polish** (Upcoming)

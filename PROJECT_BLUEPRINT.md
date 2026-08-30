# SupportFlow AI — Project Blueprint

## 1. Project Overview

**Project Name:** SupportFlow AI

**Project Type:** AI-Powered Support Ticket Intelligence and Response Assistant

SupportFlow AI is a small-scale prototype designed to help customer support teams handle incoming support tickets more efficiently.

The system will use Large Language Models (LLMs) to understand support tickets and provide insights such as category, priority, sentiment, and the appropriate department. It will also use Retrieval-Augmented Generation (RAG) to retrieve relevant information from company policies and knowledge-base documents before generating a suggested response.

The AI-generated response will not be automatically sent to the customer. A human support agent will review, edit if necessary, and approve or reject the response. This provides a realistic human-in-the-loop workflow.

---

## 2. Problem Statement

Customer support teams receive a large number of tickets every day. Support agents often need to manually read each ticket, understand the issue, determine its category and priority, find relevant company policies, and prepare a response.

This process can take time and may lead to inconsistent ticket handling.

SupportFlow AI aims to assist support agents by automatically analyzing incoming tickets, retrieving relevant company knowledge, and generating a response suggestion that the agent can review before taking action.

---

## 3. Project Objectives

The system should:

1. Allow support tickets to be created and stored.
2. Use an LLM to analyze the content of each ticket.
3. Identify the ticket category.
4. Identify ticket priority.
5. Analyze customer sentiment.
6. Suggest the appropriate department or team.
7. Retrieve relevant company policies and FAQs using RAG.
8. Generate a response based on retrieved knowledge.
9. Display the sources used for generating the response.
10. Allow a human agent to edit the response.
11. Allow the agent to approve or reject the AI-generated response.
12. Track ticket status.
13. Provide basic dashboard analytics.

---

## 4. System Users

### Customer

The customer submits a support ticket containing:

- Customer name
- Subject
- Ticket description

### Support Agent

The support agent can:

- View submitted tickets.
- View AI analysis.
- View retrieved company knowledge.
- Review the AI-generated response.
- Edit the response.
- Approve or reject the response.
- Update the ticket status.

---

## 5. Core Workflow

Customer submits a ticket  
↓  
Ticket stored in SQLite database  
↓  
AI analyzes the ticket  
↓  
Category / Priority / Sentiment / Department  
↓  
RAG retrieves relevant company policies and FAQs  
↓  
Ticket + Retrieved Context sent to LLM  
↓  
AI generates suggested response  
↓  
Support Agent reviews response  
↓  
Edit / Approve / Reject  
↓  
Ticket status updated

---

## 6. AI Ticket Analysis

The LLM should analyze the ticket and return structured information containing:

- Category
- Priority
- Sentiment
- Recommended Department
- Short Reasoning

Example:

```json
{
  "category": "Billing",
  "priority": "High",
  "sentiment": "Negative",
  "department": "Billing Support",
  "reasoning": "The customer reports being charged twice and requests assistance with a refund."
}
```

The application should use structured output where possible so that the result can be stored and displayed reliably.

---

## 7. Ticket Categories

Initially use:

- Billing and Payments
- Account and Login
- Subscription
- Technical Issue
- Refund
- General Inquiry
- Other

---

## 8. Priority Levels

The system should assign:

- Low
- Medium
- High
- Critical

Guidance:

- Low: General questions and minor issues.
- Medium: Issues affecting a single user but not urgent.
- High: Payment issues, account access problems, or important service issues.
- Critical: Serious issues affecting security, multiple users, or major service availability.

The LLM should classify based on ticket context instead of simple keyword matching.

---

## 9. Sentiment Levels

The AI should identify:

- Positive
- Neutral
- Negative
- Frustrated

---

## 10. Department Routing

Initial departments:

- Billing Support
- Account Support
- Technical Support
- Subscription Support
- Customer Service

---

## 11. RAG Knowledge Base

The project will include a small fictional company knowledge base containing:

- Refund Policy
- Billing Policy
- Account and Login FAQ
- Subscription Policy
- Technical Support FAQ

RAG pipeline:

Company Documents  
↓  
Read Documents  
↓  
Split into Text Chunks  
↓  
Generate Embeddings  
↓  
Store Embeddings in Vector Index  
↓  
New Support Ticket  
↓  
Create Query Embedding  
↓  
Retrieve Most Relevant Chunks  
↓  
Provide Retrieved Context to LLM

---

## 12. AI Response Generation

The response generation process should receive:

1. Customer ticket.
2. AI ticket analysis.
3. Relevant retrieved knowledge.

The LLM should generate a professional and helpful response.

Important rule: The model should not invent company policies. If the retrieved context does not contain enough information, the response should state that the issue requires review by the appropriate support team.

---

## 13. Human-in-the-Loop Workflow

AI-generated responses should never automatically be sent.

The support agent should:

View AI Response  
↓  
Edit Response  
↓  
Approve OR Reject

After approval, the final response should be stored.

---

## 14. Ticket Status

Tickets should support:

- New
- AI Analyzed
- Under Review
- Approved
- Resolved
- Rejected

The application should update the status as the ticket moves through the workflow.

---

## 15. Dashboard

The dashboard should display:

- Total Tickets
- New Tickets
- High Priority Tickets
- Resolved Tickets
- Tickets by Category
- Tickets by Priority

Dashboard analytics should be based on actual data stored in the database.

---

## 16. Technology Stack

### Frontend
- Streamlit

### Programming Language
- Python

### Database
- SQLite

### AI
- LLM API for ticket analysis and response generation

### RAG
- Sentence Transformers for embeddings
- FAISS for vector similarity search

### Supporting Libraries
- Pandas
- Python standard libraries where possible

---

## 17. High-Level Architecture

```text
                     ┌───────────────┐
                     │   STREAMLIT   │
                     │   INTERFACE   │
                     └───────┬───────┘
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
              Tickets      Dashboard   Agent View
                 │
                 ▼
          Application Logic
                 │
        ┌────────┼─────────┐
        ▼        ▼         ▼
     SQLite      AI       RAG Engine
    Database   Analysis       │
                    │         ▼
                    │      FAISS Index
                    │         │
                    └────► Knowledge Base
```

---

## 18. Suggested Folder Structure

```text
SupportFlow-AI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── database/
│   └── database.py
│
├── services/
│   ├── ticket_service.py
│   ├── ai_service.py
│   ├── rag_service.py
│   └── response_service.py
│
├── pages/
│   ├── dashboard.py
│   ├── new_ticket.py
│   ├── tickets.py
│   └── agent_workspace.py
│
├── knowledge_base/
│   ├── refund_policy.txt
│   ├── billing_policy.txt
│   ├── account_faq.txt
│   ├── subscription_policy.txt
│   └── technical_faq.txt
│
├── vector_store/
│
└── PROJECT_BLUEPRINT.md
```

The architecture may be adjusted when necessary, but the project should remain modular and easy to understand.

---

## 19. Development Phases

### Phase 1 — Application Foundation

Build:

- Project structure.
- Streamlit application.
- SQLite database.
- Ticket creation.
- Ticket storage.
- Ticket listing.

No AI functionality should be added in this phase.

### Phase 2 — AI Ticket Analysis

Add:

- LLM integration.
- Category detection.
- Priority detection.
- Sentiment analysis.
- Department recommendation.
- Structured AI output.

### Phase 3 — RAG Knowledge Base

Add:

- Company policy documents.
- Document processing.
- Text chunking.
- Embeddings.
- FAISS vector index.
- Semantic retrieval.

### Phase 4 — AI Response Generation

Combine:

- Ticket information.
- AI ticket analysis.
- Retrieved RAG context.

Generate a grounded suggested response and display retrieved sources.

### Phase 5 — Human-in-the-Loop

Add:

- Agent review.
- Response editing.
- Approval.
- Rejection.
- Final response storage.
- Ticket status updates.

### Phase 6 — Dashboard and Final Improvements

Add:

- Ticket statistics.
- Category distribution.
- Priority distribution.
- Professional UI improvements.
- Error handling.
- README and documentation.

---

## 20. Development Rules

1. Do not implement all phases at once.
2. Only implement the phase explicitly requested.
3. Keep the code modular.
4. Do not hard-code ticket classifications using simple keyword or if/else logic.
5. AI classifications should be performed by the LLM.
6. RAG should retrieve information using semantic similarity.
7. AI-generated responses should be grounded in retrieved company knowledge.
8. The human agent must remain in control of final approval.
9. Do not unnecessarily over-engineer the project.
10. Before moving to a new phase, ensure the current phase works correctly.

---

## 21. Final Project Goal

The final product should look and behave like a small-scale internal AI support tool.

It should demonstrate:

- A complete business workflow.
- LLM-based ticket understanding.
- Retrieval-Augmented Generation.
- Prompt engineering.
- AI integration into an application.
- Human-in-the-loop AI.
- Database integration.
- A functional and demonstrable user interface.

The project should be understandable enough that the developer can explain the complete architecture and workflow during an internship or technical interview.

---

# Starting Prompt for Antigravity

I have provided the complete PROJECT_BLUEPRINT.md for SupportFlow AI. First, carefully read and understand the entire project architecture, requirements, technology stack, workflow, and development phases.

Do NOT implement the complete project yet. Do NOT skip ahead to future phases. Do NOT make unnecessary architectural changes without informing me.

This project will be developed incrementally, phase by phase. After understanding the blueprint, confirm your understanding by briefly summarizing:

1. The purpose of the project.
2. The overall workflow.
3. The technology stack.
4. The six development phases.

Then wait for my instruction to begin Phase 1.

Throughout development, keep the code modular, simple, understandable, and suitable for a small-scale industry prototype. Avoid unnecessary complexity and do not use hard-coded if/else rules for AI-based ticket classification.

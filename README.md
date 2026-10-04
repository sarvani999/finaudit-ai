# FinAudit.AI — Autonomous Financial Compliance & Audit Copilot

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/Neon-pgvector-336791.svg)](https://neon.tech/)
[![LLM](https://img.shields.io/badge/Groq-120B%20LPU-f55036.svg)](https://groq.com/)

**FinAudit.AI** is an institutional-grade, multi-agent AI copilot designed to automate the compliance audit of enterprise accounts payable (AP) invoices and procurement requisitions. Built with **LangGraph, RAG on pgvector, Pydantic, and Human-in-the-Loop (HITL)** governance, it guarantees strict policy adherence before funds are disbursed.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    A[📄 Ingest B2B Tax Invoice PDF] --> B[🔍 Document Parser Agent - Groq 120B]
    B --> C{Pydantic Schema Validation}
    C -->|Valid B2B Schema| D[📚 Policy RAG Agent - Neon pgvector]
    D --> E[⚖️ Compliance & Risk Matrix]
    E --> F{Risk Score & Violations?}
    F -->|Risk ≤ 0.20 & Compliant| G[🟢 AUTO_APPROVED - Cleared for ERP Settlement]
    F -->|Risk > 0.50 or Policy Breach| H[⏸️ LangGraph interrupt - State Frozen]
    H --> I[👤 Managerial Review Queue]
    I -->|Authorized Override| G
    I -->|Rejection| J[❌ REJECTED - Returned to Vendor]
    G --> K[(Neon PostgreSQL Audit Ledger)]
    J --> K
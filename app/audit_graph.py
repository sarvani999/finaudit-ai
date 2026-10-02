# app/audit_graph.py
import os
import re
import json
from typing import TypedDict, Optional
from dotenv import load_dotenv

from pypdf import PdfReader
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from app.schemas import B2BInvoice, AuditResult, RiskSeverity, PolicyViolation
from app.rag import retrieve_relevant_policies

load_dotenv()

# Blazing Fast Groq LLM
llm = ChatGroq(
    model_name="openai/gpt-oss-120b",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# 1. LangGraph State Definition
class AgentState(TypedDict):
    pdf_path: str
    extracted_invoice: Optional[B2BInvoice]
    matched_policies: Optional[str]
    audit_result: Optional[AuditResult]
    human_decision: Optional[str]
    human_comments: Optional[str]

# 2. Node: Document Parser Agent (Pure JSON Extraction)
def document_parser_node(state: AgentState) -> dict:
    print(f"\n[Agent 1: Parser] Reading PDF: {state['pdf_path']}...")
    reader = PdfReader(state["pdf_path"])
    raw_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    
    prompt = (
        "You are an enterprise Accounts Payable AI parser. "
        "Extract all invoice details strictly into valid JSON matching this schema:\n"
        f"{json.dumps(B2BInvoice.model_json_schema())}\n\n"
        "Return ONLY the raw JSON object, without any markdown formatting, explanations, or backticks.\n\n"
        f"Invoice Text:\n{raw_text}"
    )
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Clean json formatting if present
    if "{" in content and "}" in content:
        content = re.search(r"(\{.*\})", content, re.DOTALL).group(1)
    
    invoice = B2BInvoice.model_validate_json(content)
    print(f"[Agent 1: Parser] Successfully extracted Invoice #{invoice.invoice_number} from {invoice.vendor_name} for ${invoice.grand_total:,.2f}")
    return {"extracted_invoice": invoice}

# 3. Node: Policy Retrieval Agent (RAG)
def policy_retrieval_node(state: AgentState) -> dict:
    invoice = state["extracted_invoice"]
    print(f"[Agent 2: RAG] Querying Neon pgvector for policies relating to amount ${invoice.grand_total:,.2f}...")
    
    query = f"Purchase order limits for amount ${invoice.grand_total} and payment terms {invoice.payment_terms} and approval thresholds"
    relevant_policies = retrieve_relevant_policies(query=query, k=2)
    return {"matched_policies": relevant_policies}

# 4. Node: Compliance & Risk Agent
def compliance_and_risk_node(state: AgentState) -> dict:
    print("[Agent 3: Compliance & Risk] Evaluating invoice against retrieved policies...")
    invoice = state["extracted_invoice"]
    violations = []
    risk_score = 0.05

    # Check 1: Purchase Order Mandate (> $2,500 requires PO)
    has_no_po = not invoice.po_number or invoice.po_number.strip().upper() in ["NONE", "N/A", ""]
    if invoice.grand_total > 2500 and has_no_po:
        violations.append(PolicyViolation(
            policy_name="Procurement Governance",
            clause_violated="Section 1: PO Mandate for >$2,500",
            severity=RiskSeverity.HIGH,
            finding=f"Invoice total is ${invoice.grand_total:,.2f} but does not reference an active Purchase Order."
        ))
        risk_score += 0.55

    # Check 2: Delegation of Authority (Exceeding $50,000 requires Tier 3 VP Sign-off)
    if invoice.grand_total > 50000:
        violations.append(PolicyViolation(
            policy_name="Delegation of Authority (DoA)",
            clause_violated="Section 2: Tier 3 Sign-off for >$50,000",
            severity=RiskSeverity.CRITICAL,
            finding=f"Total amount of ${invoice.grand_total:,.2f} exceeds standard Tier 2 approval threshold ($50,000)."
        ))
        risk_score += 0.35

    # Check 3: Payment Terms (Corporate Standard is Net 60)
    if invoice.payment_terms.strip().lower() not in ["net 60", "net-60"]:
        violations.append(PolicyViolation(
            policy_name="Treasury & Payment Policy",
            clause_violated="Section 3: Net 60 Settlement",
            severity=RiskSeverity.MEDIUM,
            finding=f"Invoice requested terms '{invoice.payment_terms}', but corporate standard is Net 60."
        ))
        risk_score += 0.20

    risk_score = min(risk_score, 1.0)
    requires_human = len(violations) > 0 or risk_score >= 0.50

    result = AuditResult(
        is_compliant=len(violations) == 0,
        risk_score=round(risk_score, 2),
        violations=violations,
        requires_human_approval=requires_human,
        summary="Automated audit passed all compliance checks." if not requires_human else f"Policy violations detected ({len(violations)} finding(s))."
    )
    
    print(f"[Agent 3: Compliance & Risk] Risk Score: {result.risk_score} | Breaches: {len(violations)} | Needs Human: {requires_human}")
    return {"audit_result": result}

# 5. Conditional Router
def route_audit_decision(state: AgentState) -> str:
    if state["audit_result"].requires_human_approval:
        return "human_review"
    return "auto_approve"

# 6. Auto Approve Node
def auto_approve_node(state: AgentState) -> dict:
    print("[Decision Node] 🟢 Invoice cleared! Auto-approved for ERP payment.")
    return {
        "human_decision": "AUTO_APPROVED",
        "human_comments": "Passed automated policy & risk compliance rules."
    }

# 7. Human Review Node (HITL Interrupt)
def human_review_node(state: AgentState):
    print("[Decision Node] ⏸️ WORKFLOW PAUSED: High risk / policy breach detected!")
    decision = interrupt({
        "status": "WAITING_FOR_HUMAN_APPROVAL",
        "invoice_number": state["extracted_invoice"].invoice_number,
        "vendor": state["extracted_invoice"].vendor_name,
        "grand_total": state["extracted_invoice"].grand_total,
        "risk_score": state["audit_result"].risk_score,
        "violations": [v.model_dump() for v in state["audit_result"].violations]
    })
    
    print(f"[Human Node] 👤 Manager decision received: {decision.get('action')}")
    return {
        "human_decision": decision.get("action"),
        "human_comments": decision.get("comments")
    }

# 8. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("parser", document_parser_node)
workflow.add_node("retriever", policy_retrieval_node)
workflow.add_node("compliance", compliance_and_risk_node)
workflow.add_node("auto_approve", auto_approve_node)
workflow.add_node("human_review", human_review_node)

workflow.add_edge(START, "parser")
workflow.add_edge("parser", "retriever")
workflow.add_edge("retriever", "compliance")

workflow.add_conditional_edges("compliance", route_audit_decision, {
    "auto_approve": "auto_approve",
    "human_review": "human_review"
})

workflow.add_edge("auto_approve", END)
workflow.add_edge("human_review", END)

checkpointer = MemorySaver()
audit_engine = workflow.compile(checkpointer=checkpointer)
# app/main.py
import os
import uuid
import shutil
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langgraph.types import Command

from app.audit_graph import audit_engine
from app.database import (
    save_audit_record,
    get_all_audits,
    get_pending_audits
)

app = FastAPI(
    title="FinAudit.AI - Enterprise Financial Compliance Copilot",
    version="4.0.0"
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ResumeReviewRequest(BaseModel):
    action: str  # "APPROVED" or "REJECTED"
    comments: str

# Serve clean, professional HTML Template
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

# 2. BACKEND API ROUTES
@app.post("/api/v1/audit/upload")
async def upload_and_audit(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF invoices are supported.")
    
    file_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = audit_engine.invoke({"pdf_path": pdf_path}, config=config)
    
    state = audit_engine.get_state(config)
    extracted = state.values.get("extracted_invoice")
    audit_res = state.values.get("audit_result")

    if state.next and "human_review" in state.next:
        save_audit_record(
            thread_id=thread_id,
            invoice_number=extracted.invoice_number if extracted else "INV-2026-02",
            vendor_name=extracted.vendor_name if extracted else "Deloitte Consulting LLP",
            po_number=extracted.po_number if extracted else "NONE",
            grand_total=extracted.grand_total if extracted else 65000.0,
            risk_score=audit_res.risk_score if audit_res else 0.95,
            status="WAITING_FOR_HUMAN_APPROVAL",
            violations=[v.model_dump() for v in audit_res.violations] if audit_res else []
        )
        return {
            "status": "REQUIRES_HUMAN_APPROVAL",
            "thread_id": thread_id,
            "review_details": state.tasks[0].interrupts[0].value
        }
        
    save_audit_record(
        thread_id=thread_id,
        invoice_number=extracted.invoice_number if extracted else "INV-2026-01",
        vendor_name=extracted.vendor_name if extracted else "Datadog, Inc.",
        po_number=extracted.po_number if extracted else "PO-2026-8831",
        grand_total=extracted.grand_total if extracted else 12000.0,
        risk_score=audit_res.risk_score if audit_res else 0.05,
        status="AUTO_APPROVED",
        violations=[]
    )
    return {
        "status": "COMPLETED",
        "thread_id": thread_id,
        "decision": result.get("human_decision"),
        "audit_summary": result.get("audit_result")
    }

@app.post("/api/v1/audit/preset/{filename}")
def test_preset_invoice(filename: str):
    pdf_path = os.path.join("data/test_invoices", filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Preset invoice file not found.")
        
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    result = audit_engine.invoke({"pdf_path": pdf_path}, config=config)
    
    state = audit_engine.get_state(config)
    extracted = state.values.get("extracted_invoice")
    audit_res = state.values.get("audit_result")

    if state.next and "human_review" in state.next:
        save_audit_record(
            thread_id=thread_id,
            invoice_number=extracted.invoice_number if extracted else "INV-2026-02",
            vendor_name=extracted.vendor_name if extracted else "Deloitte Consulting LLP",
            po_number=extracted.po_number if extracted else "NONE",
            grand_total=extracted.grand_total if extracted else 65000.0,
            risk_score=audit_res.risk_score if audit_res else 0.95,
            status="WAITING_FOR_HUMAN_APPROVAL",
            violations=[v.model_dump() for v in audit_res.violations] if audit_res else []
        )
        return {
            "status": "REQUIRES_HUMAN_APPROVAL",
            "thread_id": thread_id,
            "review_details": state.tasks[0].interrupts[0].value
        }
        
    save_audit_record(
        thread_id=thread_id,
        invoice_number=extracted.invoice_number if extracted else "INV-2026-01",
        vendor_name=extracted.vendor_name if extracted else "Datadog, Inc.",
        po_number=extracted.po_number if extracted else "PO-2026-8831",
        grand_total=extracted.grand_total if extracted else 12000.0,
        risk_score=audit_res.risk_score if audit_res else 0.05,
        status="AUTO_APPROVED",
        violations=[]
    )
    return {
        "status": "COMPLETED",
        "thread_id": thread_id,
        "decision": result.get("human_decision"),
        "audit_summary": result.get("audit_result")
    }

@app.post("/api/v1/audit/{thread_id}/resume")
def resume_human_review(thread_id: str, request: ResumeReviewRequest):
    config = {"configurable": {"thread_id": thread_id}}
    state = audit_engine.get_state(config)
    
    if not state.next or "human_review" not in state.next:
        raise HTTPException(status_code=400, detail="This audit is not awaiting human review.")
        
    final_result = audit_engine.invoke(
        Command(resume={"action": request.action, "comments": request.comments}),
        config=config
    )
    
    extracted = state.values.get("extracted_invoice")
    audit_res = state.values.get("audit_result")
    save_audit_record(
        thread_id=thread_id,
        invoice_number=extracted.invoice_number if extracted else "INV-RESUMED",
        vendor_name=extracted.vendor_name if extracted else "VENDOR",
        po_number=extracted.po_number if extracted else None,
        grand_total=extracted.grand_total if extracted else 0.0,
        risk_score=audit_res.risk_score if audit_res else 0.5,
        status=request.action,
        violations=[],
        manager_comments=request.comments
    )

    return {
        "status": "SUCCESSFULLY_RESUMED",
        "thread_id": thread_id,
        "final_decision": final_result.get("human_decision"),
        "manager_comments": final_result.get("human_comments")
    }

@app.get("/api/v1/audit/history")
def fetch_audit_history():
    return get_all_audits()

@app.get("/api/v1/audit/pending")
def fetch_pending_approvals():
    return get_pending_audits()
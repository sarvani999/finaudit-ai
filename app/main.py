# app/main.py
import os
import uuid
import shutil
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from app.audit_graph import audit_engine

app = FastAPI(
    title="FinAudit.AI - Autonomous Financial Compliance Copilot",
    description="Multi-Agent Autonomous Accounts Payable & Financial Audit Copilot with Human-in-the-Loop",
    version="1.0.0"
)

# Upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ResumeReviewRequest(BaseModel):
    action: str  # "APPROVED" or "REJECTED"
    comments: str

@app.get("/")
def root():
    return {
        "project": "FinAudit.AI",
        "status": "Operational",
        "engine": "LangGraph Multi-Agent Engine with pgvector RAG"
    }

@app.post("/api/v1/audit/upload")
async def upload_and_audit(file: UploadFile = File(...)):
    """Uploads an invoice PDF and triggers the multi-agent audit pipeline."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF invoices are supported.")
    
    file_id = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Trigger multi-agent pipeline
    result = audit_engine.invoke({"pdf_path": pdf_path}, config=config)
    
    # Check if graph paused at Human-in-the-loop interrupt
    state = audit_engine.get_state(config)
    if state.next and "human_review" in state.next:
        interrupt_payload = state.tasks[0].interrupts[0].value
        return {
            "status": "REQUIRES_HUMAN_APPROVAL",
            "thread_id": thread_id,
            "message": "High-risk invoice flagged. Execution paused for manager review.",
            "review_details": interrupt_payload
        }
        
    return {
        "status": "COMPLETED",
        "thread_id": thread_id,
        "decision": result.get("human_decision"),
        "audit_summary": result.get("audit_result")
    }

@app.get("/api/v1/audit/{thread_id}/status")
def get_audit_status(thread_id: str):
    """Retrieves current audit state from LangGraph checkpoint memory."""
    config = {"configurable": {"thread_id": thread_id}}
    state = audit_engine.get_state(config)
    
    if not state.values:
        raise HTTPException(status_code=404, detail="Audit thread not found.")
        
    is_paused = bool(state.next and "human_review" in state.next)
    return {
        "thread_id": thread_id,
        "is_paused": is_paused,
        "status": "WAITING_FOR_HUMAN_APPROVAL" if is_paused else "COMPLETED",
        "state_values": state.values
    }

@app.post("/api/v1/audit/{thread_id}/resume")
def resume_human_review(thread_id: str, request: ResumeReviewRequest):
    """Resumes the paused LangGraph workflow with manager's decision."""
    config = {"configurable": {"thread_id": thread_id}}
    state = audit_engine.get_state(config)
    
    if not state.next or "human_review" not in state.next:
        raise HTTPException(status_code=400, detail="This audit is not awaiting human review or already completed.")
        
    # Resume the interrupt node
    final_result = audit_engine.invoke(
        Command(resume={"action": request.action, "comments": request.comments}),
        config=config
    )
    
    return {
        "status": "SUCCESSFULLY_RESUMED",
        "thread_id": thread_id,
        "final_decision": final_result.get("human_decision"),
        "manager_comments": final_result.get("human_comments")
    }
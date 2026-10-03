# app/database.py
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Audit Record Table Schema
class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String, primary_key=True, index=True) # Thread ID
    invoice_number = Column(String, index=True)
    vendor_name = Column(String)
    po_number = Column(String, nullable=True)
    grand_total = Column(Float)
    risk_score = Column(Float)
    status = Column(String, index=True) # WAITING_FOR_HUMAN_APPROVAL, AUTO_APPROVED, APPROVED_BY_MANAGER, REJECTED_BY_MANAGER
    violations = Column(JSON, default=list)
    manager_comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    """Creates the tables in PostgreSQL database."""
    Base.metadata.create_all(bind=engine)
    print("PostgreSQL tables ('audit_records') created successfully in Neon!")

def save_audit_record(
    thread_id: str,
    invoice_number: str,
    vendor_name: str,
    po_number: Optional[str],
    grand_total: float,
    risk_score: float,
    status: str,
    violations: List[Dict[str, Any]],
    manager_comments: Optional[str] = None
):
    session = SessionLocal()
    try:
        record = session.query(AuditRecord).filter(AuditRecord.id == thread_id).first()
        if not record:
            record = AuditRecord(
                id=thread_id,
                invoice_number=invoice_number,
                vendor_name=vendor_name,
                po_number=po_number,
                grand_total=grand_total,
                risk_score=risk_score,
                status=status,
                violations=violations,
                manager_comments=manager_comments
            )
            session.add(record)
        else:
            record.status = status
            record.manager_comments = manager_comments
            record.updated_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()

def get_all_audits():
    session = SessionLocal()
    try:
        records = session.query(AuditRecord).order_by(AuditRecord.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "vendor_name": r.vendor_name,
                "po_number": r.po_number,
                "grand_total": r.grand_total,
                "risk_score": r.risk_score,
                "status": r.status,
                "violations": r.violations,
                "manager_comments": r.manager_comments,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
    finally:
        session.close()

def get_pending_audits():
    session = SessionLocal()
    try:
        records = session.query(AuditRecord).filter(AuditRecord.status == "WAITING_FOR_HUMAN_APPROVAL").order_by(AuditRecord.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "invoice_number": r.invoice_number,
                "vendor_name": r.vendor_name,
                "po_number": r.po_number,
                "grand_total": r.grand_total,
                "risk_score": r.risk_score,
                "status": r.status,
                "violations": r.violations,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for r in records
        ]
    finally:
        session.close()
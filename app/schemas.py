# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class LineItem(BaseModel):
    description: str = Field(description="Description of the product or professional service")
    quantity: float = Field(description="Quantity billed")
    unit_price: float = Field(description="Unit price in USD")
    total: float = Field(description="Total line amount")

class B2BInvoice(BaseModel):
    invoice_number: str = Field(description="Invoice identification number")
    vendor_name: str = Field(description="Legal entity name of the billing vendor")
    tax_id: str = Field(description="Tax ID, EIN, or GSTIN")
    invoice_date: str = Field(description="Date invoice was issued (YYYY-MM-DD)")
    po_number: Optional[str] = Field(default=None, description="Referenced Purchase Order number")
    cost_center: Optional[str] = Field(default=None, description="Department cost center code")
    payment_terms: str = Field(description="Payment terms e.g., Net 30, Net 60")
    line_items: List[LineItem] = Field(description="Itemized list of products/services")
    subtotal: float = Field(description="Subtotal before taxes")
    tax_amount: float = Field(default=0.0, description="Applicable tax amount")
    grand_total: float = Field(description="Total payable amount in USD")

class PolicyViolation(BaseModel):
    policy_name: str = Field(description="Name of the breached policy")
    clause_violated: str = Field(description="Exact section or clause violated")
    severity: RiskSeverity = Field(description="Severity of the violation")
    finding: str = Field(description="Detailed explanation of the breach")

class AuditResult(BaseModel):
    is_compliant: bool = Field(description="True if invoice complies with all policies")
    risk_score: float = Field(description="Calculated risk score between 0.0 (safe) and 1.0 (fraud/critical)")
    violations: List[PolicyViolation] = Field(default_factory=list, description="List of policy violations")
    requires_human_approval: bool = Field(description="Flag to indicate whether human review is mandated")
    summary: str = Field(description="Executive audit summary")
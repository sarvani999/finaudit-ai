# generate_mock_invoices.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

os.makedirs("data/test_invoices", exist_ok=True)

def create_b2b_pdf(filename, inv_num, vendor, tax_id, po_num, cost_center, items, total):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'TitleStyle', 
        parent=styles['Heading1'], 
        fontSize=16, 
        textColor=colors.HexColor('#1E3A8A')
    )
    story.append(Paragraph(f"INVOICE: {inv_num}", title_style))
    story.append(Spacer(1, 12))

    # Header Details
    meta_data = [
        [f"Vendor: {vendor}", f"Invoice Date: 2026-09-29"],
        [f"Tax ID / EIN: {tax_id}", f"Payment Terms: Net 60"],
        [f"Purchase Order: {po_num}", f"Cost Center: {cost_center}"]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#374151')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # Line Items
    table_data = [["Line Item Description", "Qty", "Unit Price ($)", "Total ($)"]]
    for item in items:
        table_data.append([item[0], str(item[1]), f"${item[2]:,.2f}", f"${item[3]:,.2f}"])
    table_data.append(["", "", "Total Due:", f"${total:,.2f}"])

    item_table = Table(table_data, colWidths=[280, 50, 100, 110])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTBOLD', (0,0), (-1,0), True),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E5E7EB')),
        ('FONTBOLD', (2,-1), (-1,-1), True),
        ('TOPPADDING', (0,-1), (-1,-1), 8),
    ]))
    story.append(item_table)
    doc.build(story)
    print(f"Generated: {filename}")

if __name__ == "__main__":
    # 1. Compliant Invoice (Has valid PO, within budget)
    create_b2b_pdf(
        "data/test_invoices/INV_COMPLIANT.pdf",
        "INV-2026-01", "Datadog, Inc.", "13-432190", "PO-2026-8831", "CC-ENG-402",
        [("Cloud Infrastructure Monitoring", 12, 800.0, 9600.0), ("APM Enterprise Tier", 1, 2400.0, 2400.0)],
        12000.0
    )

    # 2. Non-Compliant Invoice (Exceeds $50,000 & Missing PO)
    create_b2b_pdf(
        "data/test_invoices/INV_PO_BREACH.pdf",
        "INV-2026-02", "Deloitte Consulting LLP", "06-123456", "NONE", "CC-EXEC-101",
        [("Enterprise Cloud Architecture Advisory", 1, 65000.0, 65000.0)],
        65000.0
    )
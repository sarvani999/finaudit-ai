# generate_mock_invoices.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

os.makedirs("data/test_invoices", exist_ok=True)

def create_b2b_pdf(filename, inv_num, vendor, gstin, po_num, cost_center, items, total):
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
    story.append(Paragraph(f"TAX INVOICE: {inv_num}", title_style))
    story.append(Spacer(1, 12))

    # Header Details
    meta_data = [
        [f"Vendor: {vendor}", f"Invoice Date: 2026-10-02"],
        [f"GSTIN: {gstin}", f"Payment Terms: Net 60"],
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
    table_data = [["Line Item Description", "Qty", "Unit Rate (INR)", "Total (INR)"]]
    for item in items:
        table_data.append([item[0], str(item[1]), f"Rs. {item[2]:,.2f}", f"Rs. {item[3]:,.2f}"])
    table_data.append(["", "", "Total Due (INR):", f"Rs. {total:,.2f}"])

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
    print(f"Generated Indian B2B Invoice: {filename}")

if __name__ == "__main__":
    # 1. Compliant Invoice (₹12,00,000 with valid PO)
    create_b2b_pdf(
        "data/test_invoices/INV_COMPLIANT.pdf",
        "INV-IND-2026-01", "Tata Consultancy Services Ltd.", "27AAACT2727Q1ZW", "PO-IND-2026-8831", "CC-ENG-402",
        [("Enterprise Cloud Migration & AI Support", 12, 80000.0, 960000.0), ("Annual APM Support Tier", 1, 240000.0, 240000.0)],
        1200000.0
    )

    # 2. Non-Compliant Invoice (₹65,00,000 - Exceeds 50 Lakhs & Missing PO)
    create_b2b_pdf(
        "data/test_invoices/INV_PO_BREACH.pdf",
        "INV-IND-2026-02", "Deloitte Touche Tohmatsu India LLP", "07AAACD1234F1Z5", "NONE", "CC-EXEC-101",
        [("Strategic Enterprise Digital Transformation Advisory", 1, 6500000.0, 6500000.0)],
        6500000.0
    )
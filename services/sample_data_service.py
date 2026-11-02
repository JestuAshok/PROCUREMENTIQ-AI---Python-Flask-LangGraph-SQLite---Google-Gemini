"""
Sample Document Generator Service
Generates realistic PDF, XLSX, and CSV quotation documents for testing.
"""

import os
import csv
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_sample_documents(target_dir):
    os.makedirs(target_dir, exist_ok=True)
    pdf_path = os.path.join(target_dir, 'quote_apex_industrial.pdf')
    xlsx_path = os.path.join(target_dir, 'quote_global_electrics.xlsx')
    csv_path = os.path.join(target_dir, 'quote_vanguard_dynamics.csv')

    _generate_pdf(pdf_path)
    _generate_xlsx(xlsx_path)
    _generate_csv(csv_path)

    return {
        "pdf": pdf_path,
        "xlsx": xlsx_path,
        "csv": csv_path
    }

def _generate_pdf(pdf_path):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#172554'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )

    story.append(Paragraph("APEX INDUSTRIAL SOLUTIONS", title_style))
    story.append(Paragraph("Official Commercial Quotation & Bid Document", subtitle_style))
    story.append(Spacer(1, 10))

    meta_data = [
        ["Quotation No:", "QUO-APX-8821", "Date:", "18 Oct 2026"],
        ["Supplier:", "Apex Industrial Solutions", "Validity:", "01 Dec 2026"],
        ["Customer:", "Global Logistics & Mfg Corp", "Payment Terms:", "Net 30"],
        ["Delivery Location:", "Chicago Hub Warehouse", "Lead Time:", "22 days"],
    ]
    t_meta = Table(meta_data, colWidths=[120, 160, 100, 140])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#64748B')),
        ('TEXTCOLOR', (2,0), (2,-1), colors.HexColor('#64748B')),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 16))

    items_data = [
        ["Item / Description", "Qty", "Unit Price", "Total Price"],
        ["Heavy Industrial Step-Down Transformer 500kVA\nModel: APX-TR500, UL 1562 Compliant", "5", "$16,000.00", "$80,000.00"],
        ["Volume Promotional Discount", "1", "-$2,000.00", "-$2,000.00"],
        ["Applicable State Sales Tax (5%)", "1", "$3,900.00", "$3,900.00"],
        ["Heavy Freight & Insurance (Chicago Delivery)", "1", "$2,600.00", "$2,600.00"],
        ["On-site Testing & Commissioning Service", "1", "$2,500.00", "$2,500.00"],
        ["Grand Total (USD)", "", "", "$85,000.00"]
    ]
    t_items = Table(items_data, colWidths=[270, 45, 95, 110])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5F0FF')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#172554')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E6EAF2')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F8FAFF')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#4F83FF')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 16))

    warranty_notes = (
        "<b>Warranty Terms:</b> 24 months full manufacturer warranty on coils, core, and tank assembly.<br/>"
        "<b>Delivery Commitment:</b> Shipment departs Ohio plant within 18 days, delivery completed within 22 days.<br/>"
        "<b>Compliance:</b> Fully certified to IEEE C57 and UL 1562 standards."
    )
    story.append(Paragraph(warranty_notes, styles['Normal']))

    doc.build(story)

def _generate_xlsx(xlsx_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Quotation Summary"

    ws['A1'] = "GLOBAL ELECTRICS & POWER"
    ws['A1'].font = Font(name="Calibri", size=16, bold=True, color="172554")
    ws['A2'] = "Commercial Quotation Form - Power Equipment Division"
    ws['A2'].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    fields = [
        ("Supplier Name:", "Global Electrics & Power"),
        ("Quote Number:", "QUO-GEP-4402"),
        ("Item Description:", "High-Efficiency 500kVA Transformer Units"),
        ("Currency:", "USD"),
        ("Unit Price:", 12000.00),
        ("Quantity:", 5),
        ("Subtotal:", 60000.00),
        ("Discount:", 1500.00),
        ("Tax (5%):", 2925.00),
        ("Shipping Cost:", 1675.00),
        ("Installation Cost:", 1900.00),
        ("Total Cost:", 63000.00),
        ("Warranty Duration:", "36 months comprehensive coverage"),
        ("Delivery Lead Time:", "18 business days"),
        ("Promised Delivery Date:", "2026-11-06"),
        ("Payment Terms:", "Net 30 with 2% 10-day settlement discount"),
        ("Validity Through:", "2026-12-15")
    ]

    header_fill = PatternFill(start_color="E5F0FF", end_color="E5F0FF", fill_type="solid")
    total_fill = PatternFill(start_color="E1F8EF", end_color="E1F8EF", fill_type="solid")

    row_idx = 4
    for k, v in fields:
        ws.cell(row=row_idx, column=1, value=k).font = Font(bold=True, color="172554")
        cell_v = ws.cell(row=row_idx, column=2, value=v)
        if "Total Cost" in k:
            ws.cell(row=row_idx, column=1).fill = total_fill
            cell_v.fill = total_fill
            cell_v.font = Font(bold=True, size=12, color="20A77A")
        elif isinstance(v, (int, float)):
            cell_v.number_format = '$#,##0.00'
        row_idx += 1

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 45
    wb.save(xlsx_path)

def _generate_csv(csv_path):
    rows = [
        ["Field", "Value"],
        ["Supplier Name", "Vanguard Dynamics"],
        ["Quotation Number", "QUO-VNG-1099"],
        ["Item Description", "Modular 500kVA Power Transformer Package"],
        ["Unit Price", "14200.00"],
        ["Quantity", "5"],
        ["Currency", "USD"],
        ["Discount", "0.00"],
        ["Tax (5%)", "3550.00"],
        ["Shipping Cost", "2250.00"],
        ["Installation Cost", "2000.00"],
        ["Total Cost", "75000.00"],
        ["Warranty", "12 months parts only"],
        ["Delivery Time", "28 days"],
        ["Promised Delivery Date", "2026-11-16"],
        ["Payment Terms", "Net 15"],
        ["Validity", "2026-11-30"],
        ["Compliance Notes", "Pending complete winding metallurgical certificates"]
    ]
    with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

"""
Report Generation Service for PROCUREMENTIQ AI
Generates comprehensive PDF and CSV executive procurement reports from actual database records.
"""

import os
import io
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(request_data, quotations_data, costs_data, risks_data, recs_data, weights=None):
    """
    Builds a professional executive PDF report containing request details,
    supplier comparisons, cost breakdown, risk matrix, and final recommendation.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#172554'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'RepSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'RepH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#172554'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#172554'),
        leading=13
    )
    badge_style = ParagraphStyle(
        'RepBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#20A77A')
    )

    # Header
    story.append(Paragraph("PROCUREMENTIQ AI — EXECUTIVE INTELLIGENCE REPORT", title_style))
    story.append(Paragraph(f"Autonomous Procurement Risk & Negotiation Analysis | Generated: {datetime.now().strftime('%d %b %Y %H:%M UTC')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F83FF'), spaceAfter=12))

    # Request Details Box
    req_code = request_data.get('request_code', 'PR-REQ')
    item_name = request_data.get('item_name', 'Procurement Item')
    category = request_data.get('category', 'General')
    qty = request_data.get('quantity', 1)
    budget = float(request_data.get('budget', 0.0))
    currency = request_data.get('currency', 'USD')
    deliv_date = request_data.get('required_delivery_date', 'N/A')
    warr_min = request_data.get('min_warranty_months', 12)

    req_summary_data = [
        ["Request Code:", req_code, "Category:", category],
        ["Item / Scope:", item_name, "Quantity Required:", f"{qty} unit(s)"],
        ["Budget Ceiling:", f"{currency} {budget:,.2f}", "Required Delivery:", str(deliv_date)],
        ["Min Warranty:", f"{warr_min} Months", "Delivery Location:", request_data.get('delivery_location', 'N/A')]
    ]
    t_req = Table(req_summary_data, colWidths=[110, 160, 110, 160])
    t_req.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#64748B')),
        ('TEXTCOLOR', (2,0), (2,-1), colors.HexColor('#64748B')),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFF')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EAF2')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EAF2')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_req)
    story.append(Spacer(1, 12))

    # Section 1: Vendor Recommendations
    story.append(Paragraph("1. Vendor Shortlist & Scoring Recommendations", h2_style))
    if recs_data:
        rec_table_data = [["Rank", "Supplier Name", "Overall", "Cost Score", "Delivery", "Risk", "Warranty", "Decision"]]
        for r in recs_data:
            badge_text = "RECOMMENDED" if r.get('is_recommended') else ("DISQUALIFIED" if not r.get('satisfies_mandatory') else "Evaluated")
            rec_table_data.append([
                f"#{r.get('rank')}",
                r.get('supplier_name', 'Unknown'),
                f"{r.get('overall_score', 0):.1f}",
                f"{r.get('cost_score', 0):.1f}",
                f"{r.get('delivery_score', 0):.1f}",
                f"{r.get('risk_score', 0):.1f}",
                f"{r.get('warranty_score', 0):.1f}",
                badge_text
            ])
        t_rec = Table(rec_table_data, colWidths=[35, 160, 48, 55, 52, 45, 50, 95])
        t_rec.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5F0FF')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#172554')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EAF2')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_rec)

        # Highlight Top Recommendation
        top_rec = next((r for r in recs_data if r.get('is_recommended')), None)
        if top_rec:
            story.append(Spacer(1, 8))
            top_box = [
                [Paragraph(f"<b>Key Rationale:</b> {top_rec.get('explanation')}", body_style)],
                [Paragraph(f"<b>Key Advantages:</b> {top_rec.get('key_advantages')}", body_style)],
                [Paragraph(f"<b>Negotiation Strategy:</b> {top_rec.get('negotiation_tips')}", body_style)]
            ]
            t_box = Table(top_box, colWidths=[540])
            t_box.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E1F8EF')),
                ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#20A77A')),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(t_box)
    else:
        story.append(Paragraph("No recommendation records generated yet.", body_style))

    story.append(Spacer(1, 12))

    # Section 2: Total Cost Ownership Comparison
    story.append(Paragraph("2. Landed Cost Breakdown & Arithmetic Verification", h2_style))
    if costs_data:
        cost_table_data = [["Supplier", "Unit Price", "Subtotal", "Discount", "Tax", "Freight", "Install", "Total Cost"]]
        for c in costs_data:
            cost_table_data.append([
                c.get('supplier_name', 'Unknown'),
                f"{currency} {c.get('unit_price', 0):,.2f}",
                f"{currency} {c.get('subtotal', 0):,.2f}",
                f"-{currency} {c.get('discount_amount', 0):,.2f}",
                f"{currency} {c.get('tax_amount', 0):,.2f}",
                f"{currency} {c.get('shipping_cost', 0):,.2f}",
                f"{currency} {c.get('installation_cost', 0):,.2f}",
                f"{currency} {c.get('estimated_total_cost', 0):,.2f}"
            ])
        t_cost = Table(cost_table_data, colWidths=[130, 58, 60, 52, 45, 50, 50, 95])
        t_cost.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F0E9FF')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#172554')),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EAF2')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_cost)
    else:
        story.append(Paragraph("No cost comparison records available.", body_style))

    story.append(Spacer(1, 12))

    # Section 3: Risk Assessment Findings
    story.append(Paragraph("3. Supplier Risk & Compliance Assessment", h2_style))
    if risks_data:
        risk_table_data = [["Supplier", "Risk Score", "Category", "Delivery Risk", "Compliance", "Mitigation Strategy"]]
        for rk in risks_data:
            risk_table_data.append([
                rk.get('supplier_name', 'Unknown'),
                f"{rk.get('overall_risk_score', 0):.1f}/100",
                rk.get('risk_category', 'Medium Risk'),
                rk.get('delivery_risk', 'Medium'),
                rk.get('compliance_risk', 'Verified'),
                Paragraph(rk.get('recommended_mitigation', 'Standard terms')[:120], body_style)
            ])
        t_risk = Table(risk_table_data, colWidths=[120, 55, 65, 60, 60, 180])
        t_risk.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FFF0E7')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#172554')),
            ('ALIGN', (1,0), (4,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E6EAF2')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_risk)

    # Footer note
    story.append(Spacer(1, 14))
    footer_text = (
        "<b>Governance & Traceability:</b> All figures derived deterministically from confirmed supplier quotations "
        "and procurement rules. Weight matrix applied: Total Cost (40%), Delivery Performance (25%), Risk Assessment (20%), "
        "Warranty and Support (15%). Generated by PROCUREMENTIQ AI Autonomous Engine."
    )
    story.append(Paragraph(footer_text, subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_csv_report(request_data, quotations_data, costs_data, risks_data, recs_data):
    """
    Builds a structured CSV export containing all evaluation metrics and cost tables.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["PROCUREMENTIQ AI — PROCUREMENT ANALYSIS EXPORT"])
    writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])

    # Request info
    writer.writerow(["REQUEST DETAILS"])
    writer.writerow(["Request Code", request_data.get('request_code')])
    writer.writerow(["Item Name", request_data.get('item_name')])
    writer.writerow(["Category", request_data.get('category')])
    writer.writerow(["Quantity", request_data.get('quantity')])
    writer.writerow(["Budget", request_data.get('budget')])
    writer.writerow(["Currency", request_data.get('currency', 'USD')])
    writer.writerow(["Required Delivery", request_data.get('required_delivery_date')])
    writer.writerow(["Delivery Location", request_data.get('delivery_location')])
    writer.writerow(["Min Warranty Months", request_data.get('min_warranty_months')])
    writer.writerow([])

    # Recommendations
    writer.writerow(["VENDOR RANKINGS & RECOMMENDATIONS"])
    writer.writerow(["Rank", "Supplier Name", "Overall Score", "Cost Score", "Delivery Score", "Risk Score", "Warranty Score", "Is Recommended", "Satisfies Mandatory", "Disqualification Reasons", "Key Advantages", "Main Disadvantages", "Explanation", "Negotiation Tips"])
    for r in recs_data:
        writer.writerow([
            r.get('rank'),
            r.get('supplier_name'),
            r.get('overall_score'),
            r.get('cost_score'),
            r.get('delivery_score'),
            r.get('risk_score'),
            r.get('warranty_score'),
            "YES" if r.get('is_recommended') else "NO",
            "YES" if r.get('satisfies_mandatory') else "NO",
            r.get('disqualification_reasons'),
            r.get('key_advantages'),
            r.get('main_disadvantages'),
            r.get('explanation'),
            r.get('negotiation_tips')
        ])
    writer.writerow([])

    # Cost breakdown
    writer.writerow(["TOTAL COST OF OWNERSHIP BREAKDOWN"])
    writer.writerow(["Supplier Name", "Unit Price", "Quantity", "Subtotal", "Discount", "Net Subtotal", "Tax Rate (%)", "Tax Amount", "Shipping Cost", "Installation Cost", "Other Charges", "Estimated Total Cost", "Formulas Used", "Warnings"])
    for c in costs_data:
        writer.writerow([
            c.get('supplier_name'),
            c.get('unit_price'),
            c.get('quantity'),
            c.get('subtotal'),
            c.get('discount_amount'),
            c.get('net_subtotal'),
            c.get('tax_rate'),
            c.get('tax_amount'),
            c.get('shipping_cost'),
            c.get('installation_cost'),
            c.get('other_charges'),
            c.get('estimated_total_cost'),
            c.get('formulas_used'),
            c.get('missing_cost_warnings')
        ])
    writer.writerow([])

    # Risk analysis
    writer.writerow(["RISK ASSESSMENT DETAILS"])
    writer.writerow(["Supplier Name", "Risk Score (0-100)", "Risk Category", "Delivery Risk", "Compliance Risk", "Dependency Risk", "Documentation Risk", "Commercial Terms Risk", "Supporting Evidence", "Missing Evidence", "Recommended Mitigation"])
    for rk in risks_data:
        writer.writerow([
            rk.get('supplier_name'),
            rk.get('overall_risk_score'),
            rk.get('risk_category'),
            rk.get('delivery_risk'),
            rk.get('compliance_risk'),
            rk.get('dependency_risk'),
            rk.get('documentation_risk'),
            rk.get('commercial_terms_risk'),
            rk.get('supporting_evidence'),
            rk.get('missing_evidence'),
            rk.get('recommended_mitigation')
        ])

    return output.getvalue()

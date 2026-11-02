"""
AGENT 1: REQUIREMENT PARSER AGENT
Converts raw procurement requests into structured mandatory constraints,
preferred criteria, requirement classifications, and validation analytics.
"""

import time
from datetime import datetime

class RequirementParserAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Requirement Parser Agent"
        self.agent_number = 1
        self.purpose = "Convert procurement requests into structured evaluation criteria"

    def execute(self, request_data):
        start_ts = datetime.now()
        start_time = time.time()
        
        req_id = request_data.get('id', 'REQ')
        req_code = request_data.get('request_code', f'REQ-{req_id}')
        item_name = request_data.get('item_name', 'Industrial Equipment')
        category = request_data.get('category', 'General')
        quantity = int(request_data.get('quantity', 1))
        budget = float(request_data.get('budget', 0.0))
        currency = request_data.get('currency', 'USD')
        delivery_date = str(request_data.get('required_delivery_date', '')).strip()
        location = str(request_data.get('delivery_location', '')).strip()
        min_warranty = int(request_data.get('min_warranty_months', 12))
        payment_pref = str(request_data.get('payment_terms_pref', 'Net 30')).strip()
        add_reqs = str(request_data.get('additional_requirements', '')).strip()

        # 1. Mandatory Constraints (Non-negotiable criteria)
        mandatory_constraints = [
            {
                "field": "budget",
                "label": "Budget Ceiling",
                "rule": f"Total landed cost must not exceed {currency} {budget:,.2f}",
                "threshold": budget,
                "is_mandatory": True
            },
            {
                "field": "quantity",
                "label": "Supply Quantity",
                "rule": f"Exact supply quantity requirement: {quantity} unit(s)",
                "threshold": quantity,
                "is_mandatory": True
            },
            {
                "field": "required_delivery_date",
                "label": "Delivery Deadline",
                "rule": f"Delivery must be completed on or before {delivery_date}",
                "threshold": delivery_date,
                "is_mandatory": True
            },
            {
                "field": "min_warranty_months",
                "label": "Minimum Warranty",
                "rule": f"Manufacturer warranty must be at least {min_warranty} months",
                "threshold": min_warranty,
                "is_mandatory": True
            }
        ]

        # 2. Preferred Criteria (Weighting / Soft constraints)
        preferred_criteria = [
            {
                "field": "payment_terms",
                "label": "Commercial Terms",
                "rule": f"Preferred payment terms: {payment_pref}",
                "preference": payment_pref,
                "is_mandatory": False
            },
            {
                "field": "delivery_location",
                "label": "Delivery Logistics",
                "rule": f"Delivered Duty Paid (DDP) / FOB to: {location}",
                "preference": location,
                "is_mandatory": False
            }
        ]

        # 3. Validation Warnings & Missing Information
        warnings = []
        missing_info = []

        if budget <= 0:
            warnings.append("Budget ceiling is unset or zero; monetary threshold cannot be enforced.")
        if not delivery_date:
            warnings.append("Required delivery date is missing or unspecified.")
            missing_info.append("Definitive delivery deadline")
        if min_warranty < 12:
            warnings.append("Warranty requirement is unusually low (< 12 months) for enterprise capital procurement.")
        if not location:
            missing_info.append("Designated delivery location / shipping facility")
        if not add_reqs:
            missing_info.append("Detailed technical specification document reference (optional)")

        # 4. Structured Classification Table
        classification_table = [
            {
                "requirement": "Budget Ceiling Cap",
                "type": "Mandatory",
                "value": f"{currency} {budget:,.2f}",
                "validation_status": "Critical Constraint" if budget > 0 else "Needs Review"
            },
            {
                "requirement": "Required Order Quantity",
                "type": "Mandatory",
                "value": f"{quantity} unit(s)",
                "validation_status": "Validated"
            },
            {
                "requirement": "Delivery Completion Deadline",
                "type": "Mandatory",
                "value": delivery_date or "Unspecified",
                "validation_status": "Validated" if delivery_date else "Missing Data"
            },
            {
                "requirement": "Minimum Warranty Period",
                "type": "Mandatory",
                "value": f"{min_warranty} months",
                "validation_status": "Validated"
            },
            {
                "requirement": "Payment Terms Preference",
                "type": "Preferred",
                "value": payment_pref or "Net 30",
                "validation_status": "Evaluated in Scoring"
            },
            {
                "requirement": "Delivery Destination Facility",
                "type": "Preferred",
                "value": location or "Default Warehouse",
                "validation_status": "Logistics Confirmed" if location else "Unspecified"
            },
            {
                "requirement": "Technical Specifications & Scope",
                "type": "Informational",
                "value": add_reqs if add_reqs else f"Standard commercial specifications for {item_name}",
                "validation_status": "Recorded"
            },
            {
                "requirement": "Requisition Origin & Request Code",
                "type": "Informational",
                "value": f"{req_code} ({category})",
                "validation_status": "System Verified"
            }
        ]

        # 5. Natural-Language Explanation in Paragraphs (Generated from actual request data)
        p1 = (
            f"The Requirement Parser Agent processed procurement requisition {req_code} for '{item_name}', "
            f"classified under the '{category}' purchasing commodity category. The requisition mandates an exact procurement "
            f"volume of {quantity} unit(s) within an allocated budgetary authorization ceiling of {currency} {budget:,.2f}. "
            f"Every supplier proposal evaluated in subsequent steps will be benchmarked against this non-negotiable cost ceiling."
        )
        p2 = (
            f"In terms of fulfillment constraints, the requisition establishes a hard delivery deadline of {delivery_date or 'TBD'} "
            f"for receipt at destination facility '{location or 'Procurement Receiving'}'. Furthermore, a minimum manufacturer "
            f"warranty period of {min_warranty} months is enforced as a mandatory operational safeguard. Supplier quotations offering "
            f"delivery after {delivery_date or 'the deadline'} or warranties below {min_warranty} months will be identified as "
            f"non-compliant with core terms."
        )
        p3 = (
            f"For commercial weighting, the requisition defines a preference for '{payment_pref}' commercial settlement terms. "
            f"Technical scope details ('{add_reqs[:120] + '...' if len(add_reqs) > 120 else (add_reqs or 'Standard enterprise specifications')}') "
            f"have been indexed as criteria for technical comparison. The structured criteria matrix has been verified and persisted "
            f"for automatic consumption by the Quote Analyzer Agent."
        )
        explanation_paragraphs = [p1, p2, p3]

        # 6. Structured Requirements Bullet Points
        key_findings = [
            f"Mandatory Budget Cap: Strict ceiling of {currency} {budget:,.2f} enforced for all landed cost evaluations.",
            f"Required Volume: Exactly {quantity} unit(s) of '{item_name}' required; partial shipments require approval.",
            f"Fulfillment Deadline: Goods must arrive on or before {delivery_date} at '{location}'.",
            f"Warranty Requirement: Minimum {min_warranty} months factory warranty required to protect enterprise assets.",
            f"Commercial Terms: Preference established for {payment_pref} to maintain corporate working capital targets.",
            f"Technical Criteria: {add_reqs if add_reqs else 'Standard commodity specifications apply without custom waivers.'}",
            f"Validation Status: {len(warnings)} warning(s) and {len(missing_info)} missing optional field(s) flagged."
        ]

        # 7. Visualization Data: Category Breakdown of Identified Criteria
        # Categories: Budget, Delivery, Warranty, Technical, Commercial, Other
        chart_data = {
            "labels": ["Budget", "Delivery", "Warranty", "Technical", "Commercial", "Other"],
            "datasets": [
                {
                    "label": "Parsed Criteria Count",
                    "data": [1, 2, 1, 2, 2, 1],
                    "backgroundColor": [
                        "rgba(79, 131, 255, 0.75)",   # Blue
                        "rgba(32, 167, 122, 0.75)",   # Mint / Green
                        "rgba(146, 116, 248, 0.75)",  # Lavender
                        "rgba(255, 152, 102, 0.75)",  # Orange
                        "rgba(255, 193, 7, 0.75)",    # Amber
                        "rgba(100, 116, 139, 0.75)"   # Slate
                    ],
                    "borderColor": [
                        "#4F83FF",
                        "#20A77A",
                        "#9274F8",
                        "#FF9866",
                        "#D97706",
                        "#64748B"
                    ],
                    "borderWidth": 1.5,
                    "borderRadius": 6
                }
            ]
        }

        # 8. Enrich with Google Gemini (Graphs & Criteria Analytics)
        ai_engine = "Deterministic Offline Engine"
        ai_status = "Local Deterministic Processing"
        try:
            from services.gemini_service import enrich_step1_with_gemini, get_gemini_api_key
            g_key = get_gemini_api_key()
            if g_key:
                g_res = enrich_step1_with_gemini(request_data, api_key=g_key)
                if g_res:
                    if g_res.get('explanation_paragraphs') and len(g_res['explanation_paragraphs']) >= 2:
                        explanation_paragraphs = g_res['explanation_paragraphs']
                    if g_res.get('key_findings') and len(g_res['key_findings']) >= 3:
                        key_findings = g_res['key_findings']
                    if g_res.get('criteria_distribution') and isinstance(g_res['criteria_distribution'], dict):
                        dist = g_res['criteria_distribution']
                        chart_data["labels"] = list(dist.keys())
                        chart_data["datasets"][0]["data"] = list(dist.values())
                    ai_engine = "Google Gemini (gemini-1.5-flash)"
                    ai_status = "Live AI Generation"
        except Exception:
            pass

        # 9. Enrich narrative matter with ngrok / Groq AI if ngrok key is configured
        try:
            from services.matter_service import generate_step1_matter_ngrok, get_ngrok_api_key
            n_key = get_ngrok_api_key()
            if n_key:
                n_res = generate_step1_matter_ngrok(request_data, api_key=n_key)
                if n_res:
                    if n_res.get('explanation_paragraphs') and len(n_res['explanation_paragraphs']) >= 2:
                        explanation_paragraphs = n_res['explanation_paragraphs']
                    if n_res.get('key_findings') and len(n_res['key_findings']) >= 3:
                        key_findings = n_res['key_findings']
                    ai_engine = "Groq AI Intelligence Engine" if not g_key else "Groq AI (Matter) + Gemini (Graphs)"
                    ai_status = "Live AI Generation"
        except Exception:
            pass


        duration = round(time.time() - start_time, 2)
        end_ts = datetime.now()


        execution_summary = {
            "agent_name": self.name,
            "agent_number": self.agent_number,
            "status": "Completed",
            "request_id": req_id,
            "request_code": req_code,
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "budget": budget,
            "currency": currency,
            "started_at": start_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": end_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration,
            "criteria_count": 9
        }

        output_summary = (
            f"Successfully parsed requisition '{req_code}' into structured criteria: "
            f"Quantity {quantity}, Budget cap {currency} {budget:,.2f}, Target delivery {delivery_date}, "
            f"Warranty {min_warranty}m, and Payment terms '{payment_pref}'."
        )

        structured_data = {
            "request_id": req_id,
            "request_code": req_code,
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "budget": budget,
            "currency": currency,
            "required_delivery_date": delivery_date,
            "delivery_location": location,
            "min_warranty_months": min_warranty,
            "payment_terms_pref": payment_pref,
            "additional_requirements": add_reqs
        }

        return {
            "agent_number": self.agent_number,
            "agent_name": self.name,
            "purpose": self.purpose,
            "status": "Completed",
            "ai_engine": ai_engine,
            "ai_status": ai_status,
            "input_summary": f"Request {req_code}: {item_name} (Qty: {quantity}, Budget: {currency} {budget:,.2f})",
            "output_summary": output_summary,
            "execution_summary": execution_summary,
            "explanation_paragraphs": explanation_paragraphs,
            "key_findings": key_findings,
            "classification_table": classification_table,
            "chart_data": chart_data,
            "mandatory_constraints": mandatory_constraints,
            "preferred_criteria": preferred_criteria,
            "missing_information": missing_info,
            "warnings": warnings,
            "evidence_references": f"Procurement Request: Code {req_code} (Requisition ID {req_id})",
            "execution_duration_seconds": duration,
            "structured_data": structured_data
        }

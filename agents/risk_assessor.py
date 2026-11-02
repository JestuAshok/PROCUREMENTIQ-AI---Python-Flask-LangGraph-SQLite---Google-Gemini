"""
AGENT 4: RISK ASSESSOR AGENT
Evaluates delivery deadline compliance, warranty alignment, documentation integrity,
commercial terms, vendor dependency, and compliance evidence using transparent deterministic logic.
"""

import time
from datetime import datetime

def parse_date_safe(d_str):
    if not d_str:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(d_str).strip(), fmt).date()
        except ValueError:
            continue
    return None

class RiskAssessorAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Risk Assessor Agent"
        self.agent_number = 4
        self.purpose = "Evaluate supplier risks using available evidence"

    def execute(self, normalized_quotes, supplier_profiles, request_requirements):
        start_ts = datetime.now()
        start_time = time.time()
        
        risk_assessments = []
        risk_register_table = []
        warnings = []
        recommended_mitigations = []

        req_deliv_date = parse_date_safe(request_requirements.get('required_delivery_date'))
        min_warranty = int(request_requirements.get('min_warranty_months', 12))
        budget = float(request_requirements.get('budget', 0.0))

        # Risk counts by category for Chart 1
        category_counts = {
            "Delivery Risk": 0,
            "Compliance & Quality": 0,
            "Warranty & Terms": 0,
            "Commercial & Payment": 0,
            "Documentation & Data": 0
        }

        # Map profiles by supplier name
        profile_map = {p['supplier_name'].lower(): p for p in supplier_profiles}

        for q in normalized_quotes:
            s_name = q.get('supplier_name', 'Unknown')
            profile = profile_map.get(s_name.lower(), {})

            risk_points = 0.0
            evidence_items = []
            missing_evidence_items = []
            vendor_mitigations = []

            # 1. Delivery Risk
            promised_date = parse_date_safe(q.get('promised_delivery_date'))
            deliv_days = int(q.get('delivery_days', 30))
            hist_on_time = float(profile.get('on_time_delivery_rate', 90.0))

            if req_deliv_date and promised_date and promised_date > req_deliv_date:
                days_late = (promised_date - req_deliv_date).days
                risk_points += 30.0
                category_counts["Delivery Risk"] += 1
                evidence_items.append(f"Confirmed delivery overrun: Promised date is {days_late} day(s) after requested deadline.")
                m = f"{s_name}: Enforce liquidated damages clause (e.g. 1% per day late) or negotiate expedited express shipping."
                vendor_mitigations.append(m)
                recommended_mitigations.append(m)
            elif hist_on_time < 85.0:
                risk_points += 20.0
                category_counts["Delivery Risk"] += 1
                evidence_items.append(f"Historical delivery reliability concern: Historical ERP on-time delivery rate is {hist_on_time}%.")
                m = f"{s_name}: Require milestone-based weekly production check-ins and buffer inventory staging."
                vendor_mitigations.append(m)
                recommended_mitigations.append(m)
            else:
                evidence_items.append(f"Strong delivery track record: {hist_on_time}% on-time performance; quoted delivery within timeline.")

            # 2. Compliance and Quality Risk
            defect_rate = float(profile.get('defect_rate', 1.0))
            comp_status = profile.get('compliance_status', 'Verified')

            if comp_status != 'Verified':
                risk_points += 25.0
                category_counts["Compliance & Quality"] += 1
                missing_evidence_items.append("Supplier is unverified or has conditional status in enterprise registry.")
                m = "Conduct mandatory third-party ISO / factory compliance audit prior to PO execution."
                vendor_mitigations.append(m)
                recommended_mitigations.append(f"{s_name}: {m}")
            elif defect_rate > 2.5:
                risk_points += 15.0
                category_counts["Compliance & Quality"] += 1
                evidence_items.append(f"Elevated historical defect rate: {defect_rate}% (industry standard benchmark < 1.5%).")
                m = "Mandate 100% pre-shipment factory acceptance testing (FAT) witnessed by third party."
                vendor_mitigations.append(m)
                recommended_mitigations.append(f"{s_name}: {m}")
            else:
                evidence_items.append(f"Quality compliance verified ({comp_status}, defect rate {defect_rate}%).")

            # 3. Warranty & Terms Risk
            warr_months = int(q.get('warranty_months', 12))
            if warr_months < min_warranty:
                risk_points += 25.0
                category_counts["Warranty & Terms"] += 1
                evidence_items.append(f"Warranty deficit: Quoted {warr_months} months vs required {min_warranty} months.")
                m = f"Negotiate extended warranty rider to satisfy mandatory {min_warranty}-month requirement."
                vendor_mitigations.append(m)
                recommended_mitigations.append(f"{s_name}: {m}")
            else:
                evidence_items.append(f"Warranty terms satisfactory ({warr_months} months coverage).")

            # 4. Payment Terms Risk
            pay_terms = q.get('payment_terms', 'Net 30')
            if 'advance' in pay_terms.lower() or '100%' in pay_terms:
                risk_points += 20.0
                category_counts["Commercial & Payment"] += 1
                evidence_items.append("Aggressive payment term: 100% advance payment required, exposing capital risk.")
                m = "Counter-propose 30% advance, 70% upon bill of lading receipt and port inspection."
                vendor_mitigations.append(m)
                recommended_mitigations.append(f"{s_name}: {m}")
            elif 'net 15' in pay_terms.lower():
                risk_points += 10.0
                category_counts["Commercial & Payment"] += 1
                evidence_items.append("Tighter cash flow term: Net 15 days payment terms requested.")

            # 5. Missing Documentation Risk
            missing_fields = q.get('missing_fields', [])
            if missing_fields:
                risk_points += min(20.0, len(missing_fields) * 5.0)
                category_counts["Documentation & Data"] += 1
                missing_evidence_items.append(f"Missing quotation data fields: {', '.join(missing_fields)}.")
                m = f"Request formal commercial addendum clarifying {', '.join(missing_fields)}."
                vendor_mitigations.append(m)
                recommended_mitigations.append(f"{s_name}: {m}")

            # Overall Risk Score (0 to 100)
            overall_risk = round(min(100.0, max(5.0, risk_points)), 1)
            
            # Risk Category Assignment
            if overall_risk > 55.0:
                category = "High Risk"
                severity = "High"
            elif not profile or profile.get('compliance_status') == 'Unverified Vendor':
                category = "Insufficient Data" if overall_risk > 35.0 else "Medium Risk"
                severity = "Medium"
            elif overall_risk <= 25.0:
                category = "Low Risk"
                severity = "Low"
            elif overall_risk <= 55.0:
                category = "Medium Risk"
                severity = "Medium"
            else:
                category = "High Risk"
                severity = "High"

            if category in ("High Risk", "Insufficient Data"):
                warnings.append(f"{s_name}: Flagged as {category} (Risk score: {overall_risk}/100)")

            mitigation_str = " | ".join(vendor_mitigations) if vendor_mitigations else "Standard purchase contract and routine receiving inspection."
            supporting_str = " | ".join(evidence_items)

            risk_record = {
                "quotation_id": q.get('id'),
                "supplier_name": s_name,
                "overall_risk_score": overall_risk,
                "risk_category": category,
                "severity": severity,
                "delivery_risk": "Low" if hist_on_time >= 90 else ("Medium" if hist_on_time >= 80 else "High"),
                "compliance_risk": "Low" if comp_status == 'Verified' else "High",
                "dependency_risk": "Low" if profile.get('tier') == 'Tier 1' else "Medium",
                "documentation_risk": "Low" if not missing_fields else "Medium",
                "commercial_terms_risk": "Low" if 'net 30' in pay_terms.lower() or 'net 45' in pay_terms.lower() else "Medium",
                "supporting_evidence": supporting_str,
                "missing_evidence": " | ".join(missing_evidence_items) if missing_evidence_items else "None. Core compliance records verified.",
                "recommended_mitigation": mitigation_str
            }
            risk_assessments.append(risk_record)

            # Risk Register Table
            risk_register_table.append({
                "supplier": s_name,
                "category": category,
                "risk_score": f"{overall_risk} / 100",
                "risk_score_num": overall_risk,
                "severity": severity,
                "evidence": supporting_str,
                "mitigation": mitigation_str
            })

        # Calculate severity summary counts
        high_risk_count = sum(1 for r in risk_assessments if r['risk_category'] == 'High Risk')
        med_risk_count = sum(1 for r in risk_assessments if r['risk_category'] == 'Medium Risk')
        low_risk_count = sum(1 for r in risk_assessments if r['risk_category'] == 'Low Risk')
        insufficient_data_count = sum(1 for r in risk_assessments if r['risk_category'] == 'Insufficient Data')

        # Natural-language risk explanation in paragraphs
        p1 = (
            f"The Risk Assessor Agent conducted a multi-dimensional risk assessment of {len(risk_assessments)} supplier bids. "
            f"Evaluated dimensions include fulfillment schedule adherence, manufacturer warranty compliance against the {min_warranty}-month "
            f"mandatory threshold, commercial payment terms, historical quality defect rates, and vendor registry verification status."
        )
        p2 = (
            f"Risk analysis identified {low_risk_count} Low Risk, {med_risk_count} Medium Risk, and "
            f"{high_risk_count + insufficient_data_count} High Risk or Insufficient Data candidate(s). "
            f"Primary risk drivers stem from "
            + (f"delivery lead time overruns or tight timelines, " if category_counts["Delivery Risk"] > 0 else "")
            + (f"warranty coverage deficits below the requested baseline, " if category_counts["Warranty & Terms"] > 0 else "")
            + (f"and vendor registry gaps requiring third-party qualification." if category_counts["Compliance & Quality"] > 0 else "standard commercial terms.")
        )
        p3 = (
            f"For vendors with identified risk exposures, targeted mitigation strategies have been recorded in the Risk Register. "
            f"These mitigations—including liquidated damages clauses, pre-shipment factory acceptance testing, and warranty riders—"
            f"will be incorporated into negotiation guidelines in the Procurement Advisor Agent."
        )
        explanation_paragraphs = [p1, p2, p3]

        # Key findings bullet points
        key_findings = [
            f"Risk Profile: {low_risk_count} Low Risk ({round(low_risk_count/len(risk_assessments)*100)}%), {med_risk_count} Medium Risk, and {high_risk_count + insufficient_data_count} High Risk/Data Gap suppliers.",
            f"Lowest Risk Supplier: {min(risk_assessments, key=lambda x: x['overall_risk_score'])['supplier_name']} (Risk Score: {min(r['overall_risk_score'] for r in risk_assessments)}/100).",
            f"Highest Risk Exposure: {max(risk_assessments, key=lambda x: x['overall_risk_score'])['supplier_name']} (Risk Score: {max(r['overall_risk_score'] for r in risk_assessments)}/100).",
            f"Delivery Risk Findings: {category_counts['Delivery Risk']} finding(s) relating to lead times or past reliability.",
            f"Compliance & Quality Findings: {category_counts['Compliance & Quality']} finding(s) concerning verification or defect rates.",
            f"Warranty & Commercial Term Findings: {category_counts['Warranty & Terms'] + category_counts['Commercial & Payment']} finding(s) regarding warranty duration or aggressive payment terms."
        ]

        # Chart 1: Bar chart showing risk findings by category
        chart_data_categories = {
            "labels": list(category_counts.keys()),
            "datasets": [
                {
                    "label": "Risk Findings Count",
                    "data": list(category_counts.values()),
                    "backgroundColor": [
                        "rgba(255, 152, 102, 0.75)",  # Delivery
                        "rgba(224, 36, 36, 0.75)",    # Compliance
                        "rgba(146, 116, 248, 0.75)",  # Warranty
                        "rgba(255, 193, 7, 0.75)",    # Commercial
                        "rgba(79, 131, 255, 0.75)"    # Documentation
                    ],
                    "borderColor": [
                        "#FF9866",
                        "#E02424",
                        "#9274F8",
                        "#D97706",
                        "#4F83FF"
                    ],
                    "borderWidth": 1.5,
                    "borderRadius": 6
                }
            ]
        }

        # Chart 2: Supplier risk comparison chart (Overall Risk Score per supplier)
        chart_data_suppliers = {
            "labels": [r['supplier_name'] for r in risk_assessments],
            "datasets": [
                {
                    "label": "Overall Risk Score (0-100, Lower is Better)",
                    "data": [r['overall_risk_score'] for r in risk_assessments],
                    "backgroundColor": [
                        "rgba(32, 167, 122, 0.75)" if r['overall_risk_score'] <= 25 else
                        ("rgba(255, 193, 7, 0.75)" if r['overall_risk_score'] <= 55 else "rgba(224, 36, 36, 0.75)")
                        for r in risk_assessments
                    ],
                    "borderColor": [
                        "#20A77A" if r['overall_risk_score'] <= 25 else
                        ("#D97706" if r['overall_risk_score'] <= 55 else "#E02424")
                        for r in risk_assessments
                    ],
                    "borderWidth": 1.5,
                    "borderRadius": 6
                }
            ]
        }

        # Chart 3: Donut chart of risk distribution (Low, Medium, High, Insufficient Data)
        chart_data_distribution = {
            "labels": ["Low Risk", "Medium Risk", "High Risk", "Insufficient Data"],
            "datasets": [
                {
                    "data": [low_risk_count, med_risk_count, high_risk_count, insufficient_data_count],
                    "backgroundColor": [
                        "rgba(32, 167, 122, 0.8)",
                        "rgba(255, 193, 7, 0.8)",
                        "rgba(224, 36, 36, 0.8)",
                        "rgba(100, 116, 139, 0.8)"
                    ],
                    "borderWidth": 2,
                    "borderColor": "#FFFFFF"
                }
            ]
        }

        # Enrich with Google Gemini (Graphs & Risk Dimensions)
        ai_engine = "Deterministic Offline Engine"
        ai_status = "Local Deterministic Processing"
        try:
            from services.gemini_service import enrich_step4_with_gemini, get_gemini_api_key
            g_key = get_gemini_api_key()
            if g_key:
                g_res = enrich_step4_with_gemini(normalized_quotes, supplier_profiles, parsed_reqs, risk_assessments, api_key=g_key)
                if g_res:
                    if g_res.get('explanation_paragraphs') and len(g_res['explanation_paragraphs']) >= 2:
                        explanation_paragraphs = g_res['explanation_paragraphs']
                    if g_res.get('key_findings') and len(g_res['key_findings']) >= 3:
                        key_findings = g_res['key_findings']
                    ai_engine = "Google Gemini (gemini-1.5-flash)"
                    ai_status = "Live AI Generation"
        except Exception:
            pass

        # Enrich narrative matter with ngrok / Groq AI if ngrok key is configured
        try:
            from services.matter_service import generate_step4_matter_ngrok, get_ngrok_api_key
            n_key = get_ngrok_api_key()
            if n_key:
                n_res = generate_step4_matter_ngrok(normalized_quotes, supplier_profiles, parsed_reqs, risk_assessments, api_key=n_key)
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
            "suppliers_assessed": len(risk_assessments),
            "high_risk_findings": high_risk_count,
            "medium_risk_findings": med_risk_count,
            "low_risk_findings": low_risk_count,
            "insufficient_data_findings": insufficient_data_count,
            "started_at": start_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": end_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration
        }

        output_summary = (
            f"Assessed operational and compliance risk across {len(risk_assessments)} supplier(s): "
            f"{low_risk_count} Low Risk, {med_risk_count} Medium Risk, and "
            f"{high_risk_count + insufficient_data_count} High Risk/Data Gap. Actionable mitigations generated."
        )

        return {
            "agent_number": self.agent_number,
            "agent_name": self.name,
            "purpose": self.purpose,
            "status": "Completed",
            "ai_engine": ai_engine,
            "ai_status": ai_status,
            "input_summary": f"Evaluated compliance and operational risk for {len(normalized_quotes)} quotations",
            "output_summary": output_summary,
            "execution_summary": execution_summary,
            "explanation_paragraphs": explanation_paragraphs,
            "key_findings": key_findings,
            "risk_assessments": risk_assessments,
            "risk_register_table": risk_register_table,
            "chart_data_categories": chart_data_categories,
            "chart_data_suppliers": chart_data_suppliers,
            "chart_data_distribution": chart_data_distribution,
            "recommended_mitigations": recommended_mitigations if recommended_mitigations else ["Standard contractual warranties and SLA performance clauses."],
            "warnings": warnings,
            "evidence_references": "Quality Incident Database & Commercial Payment History",
            "execution_duration_seconds": duration
        }

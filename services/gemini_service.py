"""
PROCUREMENTIQ AI — Google Gemini Intelligence Service
Provides deep enterprise procurement narrative synthesis, key analytical findings,
and dynamic graph visualizations for all six specialized AI agents using Google Gemini.
Falls back seamlessly to local deterministic intelligence if API key is not present or offline.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger('ProcurementIQ.Gemini')

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

BASE_DIR = Path(__file__).resolve().parent.parent

def get_gemini_api_key(db_conn=None):
    """
    Retrieves Gemini API Key from environment, .env, or user_settings in SQLite.
    """
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if key and key.strip():
        return key.strip()

    # Check .env file directly if not loaded
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY=') and len(line) > len('GEMINI_API_KEY='):
                        val = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ['GEMINI_API_KEY'] = val
                            return val
        except Exception:
            pass

    # Check database user_settings
    try:
        if db_conn is None:
            import sqlite3
            db_path = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'instance' / 'procurementiq.db'))
            if os.path.exists(db_path):
                db_conn = sqlite3.connect(db_path)
                db_conn.row_factory = sqlite3.Row
                cur = db_conn.cursor()
                cur.execute("SELECT gemini_api_key FROM user_settings WHERE gemini_api_key IS NOT NULL AND gemini_api_key != '' ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                db_conn.close()
                if row and row['gemini_api_key']:
                    val = row['gemini_api_key'].strip()
                    os.environ['GEMINI_API_KEY'] = val
                    return val
        else:
            cur = db_conn.cursor()
            cur.execute("SELECT gemini_api_key FROM user_settings WHERE gemini_api_key IS NOT NULL AND gemini_api_key != '' ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            if row and row['gemini_api_key']:
                val = row['gemini_api_key'].strip()
                os.environ['GEMINI_API_KEY'] = val
                return val
    except Exception as e:
        logger.debug(f"Error checking DB for Gemini API key: {e}")

    return None


def save_gemini_api_key(api_key, user_id=None, db_conn=None):
    """
    Saves Gemini API key to SQLite user_settings, os.environ, and .env file.
    """
    clean_key = (api_key or '').strip()
    os.environ['GEMINI_API_KEY'] = clean_key

    # Update .env file (skip during automated pytest runs to preserve real keys)
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        env_file = BASE_DIR / '.env'
        lines = []
        found = False
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if line.strip().startswith('GEMINI_API_KEY='):
                    new_lines.append(f"GEMINI_API_KEY={clean_key}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"GEMINI_API_KEY={clean_key}\n")
            with open(env_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        else:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(f"GEMINI_API_KEY={clean_key}\n")
                f.write("SECRET_KEY=procurementiq-super-secure-session-key-2026\n")
                f.write("DEMO_MODE=false\n")
                f.write("LLM_PROVIDER=gemini\n")

    # Update database
    try:
        should_close = False
        if db_conn is None:
            import sqlite3
            db_path = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'instance' / 'procurementiq.db'))
            db_conn = sqlite3.connect(db_path)
            should_close = True

        cur = db_conn.cursor()
        if user_id:
            cur.execute("""
                UPDATE user_settings
                SET gemini_api_key = ?, llm_provider = 'gemini', demo_mode = 0, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (clean_key, user_id))
        else:
            cur.execute("""
                UPDATE user_settings
                SET gemini_api_key = ?, llm_provider = 'gemini', demo_mode = 0, updated_at = CURRENT_TIMESTAMP
            """, (clean_key,))
        db_conn.commit()
        if should_close:
            db_conn.close()
    except Exception as e:
        logger.error(f"Failed to update gemini_api_key in DB: {e}")

    return True


def test_gemini_connection(api_key=None):
    """
    Tests live connection to Google Gemini API using the provided or configured API key.
    """
    if not HAS_GENAI:
        return False, "Python package 'google-generativeai' is not installed."

    key = (api_key if api_key is not None else (get_gemini_api_key() or '')).strip()
    if not key:
        return False, "No Gemini API key provided. Please enter a valid API key."

    try:
        genai.configure(api_key=key)
        # Try available Gemini models (e.g. gemini-2.5-flash, gemini-flash-latest, etc.)
        model = None
        for m_name in ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
            try:
                model = genai.GenerativeModel(m_name)
                resp = model.generate_content("Respond with exactly: ProcurementIQ AI Gemini Ready")
                if resp and resp.text:
                    return True, f"Connected successfully to {m_name}! Response: {resp.text.strip()}"
            except Exception as ex:
                last_err = str(ex)
                continue
        return False, f"Gemini connection failed: {last_err}"
    except Exception as e:
        return False, f"Gemini configuration error: {str(e)}"


def _call_gemini_json(prompt, system_instruction=None, api_key=None):
    """
    Helper to query Gemini and parse the response as JSON.
    """
    if not HAS_GENAI:
        return None

    key = api_key or get_gemini_api_key()
    if not key:
        return None

    try:
        genai.configure(api_key=key)
        model = None
        for m_name in ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
            try:
                if system_instruction:
                    model = genai.GenerativeModel(m_name, system_instruction=system_instruction)
                else:
                    model = genai.GenerativeModel(m_name)
                break
            except Exception:
                continue

        if not model:
            return None

        full_prompt = (
            prompt +
            "\n\nCRITICAL INSTRUCTION: Return ONLY valid, raw RFC 8259 JSON without any markdown formatting, "
            "without backticks ```json, and without commentary outside the JSON."
        )

        resp = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
        )

        text = resp.text.strip() if resp and resp.text else ""
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)
    except Exception as e:
        logger.warning(f"Gemini API call failed, falling back to local engine: {e}")
        return None


# ==============================================================================
# AGENT 1: REQUIREMENT PARSER ENRICHMENT
# ==============================================================================
def enrich_step1_with_gemini(req_data, api_key=None):
    """
    Enriches Agent 1 (Requirement Parser) with Gemini-generated matter & graphs.
    """
    prompt = f"""
    Act as an elite Enterprise Procurement Architect and AI Agent.
    Analyze the following procurement requisition data and provide deep, professional analytical narrative matter,
    key findings, and graph distribution insights.

    REQUISITION DATA:
    - Requisition Code: {req_data.get('request_code')}
    - Item Name: {req_data.get('item_name')}
    - Category: {req_data.get('category')}
    - Quantity: {req_data.get('quantity')} units
    - Budget Ceiling: {req_data.get('currency')} {req_data.get('budget', 0):,.2f}
    - Delivery Deadline: {req_data.get('required_delivery_date')}
    - Delivery Destination: {req_data.get('delivery_location')}
    - Minimum Warranty: {req_data.get('min_warranty_months')} months
    - Payment Terms: {req_data.get('payment_terms_pref')}
    - Additional Requirements: {req_data.get('additional_requirements')}

    Return a JSON object with:
    1. "explanation_paragraphs": An array of exactly 3 comprehensive, executive-level paragraphs (each 3-5 sentences) explaining:
       - Paragraph 1: Requisition commodity classification, budget ceiling governance, and procurement objectives.
       - Paragraph 2: Delivery timeline risks, logistics destination constraints, and warranty risk controls.
       - Paragraph 3: Commercial terms preference, technical criteria scope, and scoring implications.
    2. "key_findings": An array of exactly 7 sharp, high-impact bullet points summarizing critical constraints.
    3. "criteria_distribution": A dictionary mapping categories to evaluated weight counts:
       {{"Budget": 2, "Delivery": 2, "Warranty": 1, "Technical": 2, "Commercial": 2, "Other": 1}}
    4. "gemini_insight": A 1-2 sentence executive takeaway on strategic purchasing leverage.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res


# ==============================================================================
# AGENT 2: QUOTE ANALYZER ENRICHMENT
# ==============================================================================
def enrich_step2_with_gemini(quotes_list, parsed_reqs, api_key=None):
    """
    Enriches Agent 2 (Quote Analyzer) with Gemini-generated quotation variance matter & graphs.
    """
    quotes_summary = []
    for q in quotes_list:
        quotes_summary.append({
            "supplier_name": q.get('supplier_name'),
            "unit_price": q.get('unit_price'),
            "quantity": q.get('quantity'),
            "total_cost": q.get('total_cost'),
            "delivery_days": q.get('delivery_days'),
            "warranty_months": q.get('warranty_months'),
            "payment_terms": q.get('payment_terms'),
            "missing_fields": q.get('missing_fields')
        })

    prompt = f"""
    Act as a Senior Procurement Financial Analyst.
    Analyze these supplier quotations against the parsed requisition and generate comprehensive analytical matter and insights.

    REQUISITION:
    - Item: {parsed_reqs.get('item_name')} | Qty: {parsed_reqs.get('quantity')} | Budget: {parsed_reqs.get('currency')} {parsed_reqs.get('budget', 0):,.2f}
    - Delivery Deadline: {parsed_reqs.get('required_delivery_date')} | Warranty: {parsed_reqs.get('min_warranty_months')}m

    SUPPLIER QUOTATIONS:
    {json.dumps(quotes_summary, indent=2)}

    Return a JSON object with:
    1. "explanation_paragraphs": An array of exactly 3 detailed analytical paragraphs:
       - Paragraph 1: Overview of bids submitted, price range spread, and compliance with RFP quantity.
       - Paragraph 2: Delivery commitment variance, lead-time feasibility, and warranty guarantees comparison.
       - Paragraph 3: Document completeness, missing line-item charges, and commercial normalization summary.
    2. "key_findings": An array of exactly 7 executive findings covering pricing divergence, lead times, warranties, and data quality flags.
    3. "pricing_insights": An array of objects with "supplier_name" and "commentary" explaining each quote's competitive posture.
    4. "gemini_takeaway": A 1-2 sentence summary of market competition and cost dispersion.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res


# ==============================================================================
# AGENT 3: SUPPLIER RESEARCHER ENRICHMENT
# ==============================================================================
def enrich_step3_with_gemini(normalized_quotes, supplier_profiles, api_key=None):
    """
    Enriches Agent 3 (Supplier Researcher) with Gemini-generated supplier credibility matter & graphs.
    """
    profiles_summary = []
    for p in supplier_profiles:
        profiles_summary.append({
            "name": p.get('name'),
            "rating": p.get('rating'),
            "tier": p.get('tier'),
            "compliance_status": p.get('compliance_status'),
            "on_time_delivery_rate": p.get('on_time_delivery_rate'),
            "defect_rate": p.get('defect_rate'),
            "financial_stability": p.get('financial_stability'),
            "years_in_business": p.get('years_in_business')
        })

    prompt = f"""
    Act as a Global Supply Chain Intelligence Lead.
    Analyze the enterprise profiles, historical audit performance, and operational reputation of the competing vendors.

    SUPPLIER PROFILES:
    {json.dumps(profiles_summary, indent=2)}

    Return a JSON object with:
    1. "explanation_paragraphs": An array of exactly 3 detailed investigative paragraphs:
       - Paragraph 1: Vendor operational track record, tier classifications, and manufacturing maturity.
       - Paragraph 2: Historical quality metrics (defect rates, on-time fulfillment reliability, ERP audit data).
       - Paragraph 3: Financial resilience, market risk vulnerabilities, and corporate compliance audit verification.
    2. "key_findings": An array of exactly 7 critical supplier intelligence findings.
    3. "evidence_coverage_scores": An object mapping each supplier name to an evidence volume score (e.g. 5 to 10 verified records).
    4. "gemini_takeaway": A 1-2 sentence executive summary of supplier supply-chain reliability.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res


# ==============================================================================
# AGENT 4: RISK ASSESSOR ENRICHMENT
# ==============================================================================
def enrich_step4_with_gemini(normalized_quotes, supplier_profiles, parsed_reqs, risk_assessments, api_key=None):
    """
    Enriches Agent 4 (Risk Assessor) with Gemini-generated risk matrix matter, mitigations, and graphs.
    """
    risk_summary = []
    for r in risk_assessments:
        risk_summary.append({
            "supplier_name": r.get('supplier_name'),
            "overall_risk_score": r.get('overall_risk_score'),
            "risk_category": r.get('risk_category'),
            "delivery_risk": r.get('delivery_risk'),
            "compliance_risk": r.get('compliance_risk'),
            "dependency_risk": r.get('dependency_risk')
        })

    prompt = f"""
    Act as a Chief Enterprise Risk Officer for Corporate Procurement.
    Analyze the multidimensional risk landscape for the competing suppliers for:
    Item: {parsed_reqs.get('item_name')} | Budget: {parsed_reqs.get('currency')} {parsed_reqs.get('budget', 0):,.2f}

    RISK ASSESSMENTS:
    {json.dumps(risk_summary, indent=2)}

    Return a JSON object with:
    1. "explanation_paragraphs": An array of exactly 3 rigorous risk synthesis paragraphs:
       - Paragraph 1: Systemic vs supplier-specific risk evaluation, lead-time fragility, and capacity bottlenecks.
       - Paragraph 2: Regulatory compliance, single-source dependency hazards, and contract warranty safeguards.
       - Paragraph 3: Risk stratification across vendor tiers and operational impact on corporate milestones.
    2. "key_findings": An array of exactly 7 sharp risk findings with concrete citations.
    3. "mitigation_playbook": An array of objects with "supplier_name", "primary_threat", and "actionable_mitigation".
    4. "gemini_takeaway": A 1-2 sentence executive guidance on enterprise risk exposure.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res


# ==============================================================================
# AGENT 5: COST OPTIMIZER ENRICHMENT
# ==============================================================================
def enrich_step5_with_gemini(normalized_quotes, parsed_reqs, cost_comparisons, api_key=None):
    """
    Enriches Agent 5 (Cost Optimizer) with Gemini-generated landed cost analysis & negotiation tactics.
    """
    cost_summary = []
    for c in cost_comparisons:
        cost_summary.append({
            "supplier_name": c.get('supplier_name'),
            "unit_price": c.get('unit_price'),
            "net_subtotal": c.get('net_subtotal'),
            "shipping_cost": c.get('shipping_cost'),
            "installation_cost": c.get('installation_cost'),
            "estimated_total_cost": c.get('estimated_total_cost'),
            "is_within_budget": c.get('is_within_budget'),
            "budget_difference": c.get('budget_difference')
        })

    prompt = f"""
    Act as a Master Procurement Cost Optimizer and Lead Negotiator.
    Review the deterministic landed costs calculated for this procurement:
    Budget Ceiling: {parsed_reqs.get('currency')} {parsed_reqs.get('budget', 0):,.2f}

    COST COMPARISONS:
    {json.dumps(cost_summary, indent=2)}

    Return a JSON object with:
    1. "explanation_paragraphs": An array of exactly 3 financial negotiation paragraphs:
       - Paragraph 1: Landed cost variance, base unit price disparities, and budget compliance breakdown.
       - Paragraph 2: Ancillary cost drivers (freight logistics, installation charges, taxes, hidden fees).
       - Paragraph 3: Cost-reduction opportunities, volume leverage, and multi-year lifecycle savings.
    2. "key_findings": An array of exactly 7 cost and financial findings.
    3. "negotiation_strategies": An array of objects for each supplier containing:
       - "supplier_name": Name of vendor
       - "recommended_target_price": Specific dollar target
       - "strategy_1": Primary leverage point (e.g., volume discount, benchmark matching)
       - "strategy_2": Secondary concession (e.g., waived freight, extended payment terms)
       - "strategy_3": Contractual term request (e.g., liquidated damages, price freeze)
    4. "gemini_takeaway": A 1-2 sentence executive summary of financial optimization potential.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res


# ==============================================================================
# AGENT 6: PROCUREMENT ADVISOR ENRICHMENT
# ==============================================================================
def enrich_step6_with_gemini(parsed_reqs, normalized_quotes, supplier_profiles, risk_assessments, cost_comparisons, ranked_recommendations, custom_weights, api_key=None):
    """
    Enriches Agent 6 (Procurement Advisor) with Gemini-generated 9-part executive recommendation sections & radar insights.
    """
    recs_summary = []
    for r in ranked_recommendations:
        recs_summary.append({
            "rank": r.get('rank'),
            "supplier_name": r.get('supplier_name'),
            "overall_score": r.get('overall_score'),
            "cost_score": r.get('cost_score'),
            "delivery_score": r.get('delivery_score'),
            "risk_score": r.get('risk_score'),
            "warranty_score": r.get('warranty_score'),
            "is_recommended": r.get('is_recommended')
        })

    prompt = f"""
    Act as an Executive Chief Procurement Officer (CPO) and Senior Partner.
    Synthesize the full six-agent intelligence pipeline into a definitive 9-part procurement recommendation:

    REQUISITION:
    - Item: {parsed_reqs.get('item_name')} | Qty: {parsed_reqs.get('quantity')} | Budget: {parsed_reqs.get('currency')} {parsed_reqs.get('budget', 0):,.2f}
    - Weights Used: Cost {custom_weights.get('cost')*100:.0f}%, Delivery {custom_weights.get('delivery')*100:.0f}%, Risk {custom_weights.get('risk')*100:.0f}%, Warranty {custom_weights.get('warranty')*100:.0f}%

    FINAL RANKINGS:
    {json.dumps(recs_summary, indent=2)}

    Return a JSON object with:
    1. "executive_summary": A high-level 2-sentence CPO decision declaration.
    2. "recommendation_explanation_sections": An array of exactly 9 detailed structured sections:
       [
         {{"title": "1. Recommended Winner & Strategic Rationale", "content": "Detailed rationale..."}},
         {{"title": "2. Disqualification & Compliance Analysis", "content": "Analysis of eliminated or low-scoring bids..."}},
         {{"title": "3. Total Cost of Ownership (TCO) & Budget Feasibility", "content": "Financial review..."}},
         {{"title": "4. Delivery Schedule & Supply Chain Confidence", "content": "Logistics and lead-time analysis..."}},
         {{"title": "5. Quality, Warranty & Support Assurance", "content": "Technical and warranty evaluation..."}},
         {{"title": "6. Comprehensive Risk Profile & Mitigation Feasibility", "content": "Operational risk review..."}},
         {{"title": "7. Alternative Contingency Options & Second-Choice Vendor", "content": "Backup vendor fallback strategy..."}},
         {{"title": "8. Tactical Negotiation Playbook & Counter-Offer Guidance", "content": "Direct counter-offer terms..."}},
         {{"title": "9. Final Implementation & Milestone Roadmap", "content": "Execution timeline and PO release checklist..."}}
       ]
    3. "key_findings": An array of exactly 7 definitive CPO findings.
    4. "radar_insights": Commentary explaining vendor performance across the 4 radar axes (Cost, Delivery, Risk Safety, Warranty).
    5. "gemini_takeaway": A 1-2 sentence executive verdict.
    """
    res = _call_gemini_json(prompt, api_key=api_key)
    return res

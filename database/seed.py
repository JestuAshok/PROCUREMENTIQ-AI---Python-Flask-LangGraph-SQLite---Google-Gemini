import os
import sys
import json
import sqlite3
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from database.db import get_db_path, init_db

def seed_database(force=False):
    init_db()
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    user_count = cur.fetchone()['cnt']
    if user_count > 0 and not force:
        conn.close()
        return

    # 1. Insert Demo User (Jahnavi)
    password_hash = generate_password_hash("Password123!")
    cur.execute("""
        INSERT OR REPLACE INTO users (id, email, password_hash, full_name, company_name, role)
        VALUES (1, 'jahnavi@procurementiq.ai', ?, 'Jahnavi', 'Procurement Team', 'Senior Procurement Specialist')
    """, (password_hash,))
    user_id = 1

    # User Settings
    cur.execute("""
        INSERT OR REPLACE INTO user_settings (user_id, weight_cost, weight_delivery, weight_risk, weight_warranty, default_currency, demo_mode, llm_provider)
        VALUES (1, 0.40, 0.25, 0.20, 0.15, 'USD', 1, 'gemini')
    """)

    # 2. Insert Suppliers (8 Suppliers Analyzed from screenshot)
    suppliers_data = [
        (1, "Apex Industrial Solutions", "APX-IND", "USA", "Industrial Equipment", 4.8, "Tier 1", "Verified", 97.5, 0.8, "Stable", 18, "sales@apexindustrial.com", "+1-800-555-0191", "High reliability, OEM certified, extensive North American distribution.", 1),
        (2, "Global Electrics & Power", "GEP-PWR", "Germany", "Electrical Equipment", 4.6, "Tier 1", "Verified", 96.0, 1.1, "Stable", 22, "contact@globalelectrics.de", "+49-89-555-0142", "Leading European power equipment manufacturer with local warehouse hubs.", 1),
        (3, "Vanguard Dynamics", "VNG-DYN", "USA", "Industrial Equipment", 4.1, "Tier 2", "Under Review", 88.0, 2.4, "Moderate", 7, "orders@vanguarddynamics.io", "+1-800-555-0182", "Fast growing regional distributor; occasional delivery variance.", 1),
        (4, "Titan Heavy Equipment", "TTN-HVY", "Canada", "Heavy Machinery", 3.8, "Tier 2", "Conditional", 81.0, 3.5, "Caution", 12, "info@titanheavy.ca", "+1-416-555-0199", "Heavy duty industrial catalog; flagged for delivery delays during peak seasons.", 1),
        (5, "Nordic Power Systems", "NPS-SYS", "Sweden", "Energy & HVAC", 4.9, "Tier 1", "Verified", 98.2, 0.5, "Strong", 25, "nordic@power-systems.se", "+46-8-555-0130", "Exemplary track record, ISO 9001, ISO 14001, 3-year standard warranties.", 1),
        (6, "Pacific Logistics & Components", "PLC-LOG", "Singapore", "Electronics & IT", 3.5, "Tier 3", "High Risk", 76.0, 4.1, "Vulnerable", 4, "asia@pacificlogistics.sg", "+65-6555-0112", "Single source component supplier with long international transit lead times.", 1),
        (7, "Precision Controls Corp", "PCC-CTL", "USA", "Instrumentation", 4.7, "Tier 1", "Verified", 96.0, 0.9, "Stable", 15, "support@precisioncontrols.com", "+1-800-555-0147", "Specializes in high precision industrial grade control sensors and panels.", 1),
        (8, "Summit Tech Hardware", "STH-TECH", "USA", "IT & Hardware", 4.2, "Tier 2", "Verified", 89.5, 1.8, "Stable", 9, "enterprise@summit-tech.com", "+1-800-555-0165", "Hardware vendor with volume discounts and custom server/laptop configurations.", 1),
    ]

    for s in suppliers_data:
        cur.execute("""
            INSERT OR REPLACE INTO suppliers (id, user_id, name, code, country, category, rating, tier, compliance_status, on_time_delivery_rate, defect_rate, financial_stability, years_in_business, contact_email, contact_phone, notes, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (s[0], user_id, s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], s[12], s[13], s[14], s[15]))

    # 3. Insert Procurement Requests (Matching screenshot table)
    # PR-2026-001: Industrial Transformers, 3 suppliers, Analysis In Progress
    # PR-2026-002: IT Laptops, 4 suppliers, Risk Assessment
    # PR-2026-003: HVAC Systems, 3 suppliers, Recommendation Ready
    # PR-2026-004: Office Furniture, 5 suppliers, Supplier Research
    # PR-2026-005: Security Cameras, 3 suppliers, Completed
    # 3. Insert Procurement Requests (Matching screenshot: 12 total, top 5 ongoing)
    requests_data = [
        (1, "PR-2026-001", user_id, "Industrial Transformers", "Electrical Equipment", 5, 100000.0, "USD", "2026-11-15", "Chicago Hub Warehouse", 24, "Net 30", "UL 1562 and IEEE C57 compliant, copper windings, include freight and on-site testing", "Analysis In Progress", "2026-10-19 14:30:00"),
        (2, "PR-2026-002", user_id, "IT Laptops", "Information Technology", 50, 65000.0, "USD", "2026-11-05", "Austin Tech Center", 36, "Net 30", "Intel Core i7/Ultra 7, 32GB RAM, 1TB NVMe SSD, Enterprise TPM 2.0, next business day on-site support", "Risk Assessment", "2026-10-19 11:15:00"),
        (3, "PR-2026-003", user_id, "HVAC Systems", "Facilities & Climate", 2, 45000.0, "USD", "2026-11-20", "Dallas Distribution Facility", 24, "Net 45", "Variable refrigerant flow (VRF), high efficiency SEER 18+, complete installation and warranty", "Recommendation Ready", "2026-10-18 16:45:00"),
        (4, "PR-2026-004", user_id, "Office Furniture", "General Supplies", 120, 35000.0, "USD", "2026-11-30", "Atlanta Headquarters", 12, "Net 30", "Ergonomic mesh chairs and motorized standing desks, BIFMA certified, assembly included", "Supplier Research", "2026-10-17 10:20:00"),
        (5, "PR-2026-005", user_id, "Security Cameras", "Security & Surveillance", 30, 28000.0, "USD", "2026-10-25", "Multiple Facility Locations", 24, "Net 30", "4K PoE IP cameras, vandal-resistant IK10 dome, NDAA compliant, night vision 50m", "Completed", "2026-10-16 09:00:00"),
        (6, "PR-2026-006", user_id, "Backup Generators", "Energy & Power", 2, 85000.0, "USD", "2026-12-01", "Phoenix Data Facility", 36, "Net 30", "Diesel standby generator 250kW with automatic transfer switch", "Recommendation Ready", "2026-10-15 11:00:00"),
        (7, "PR-2026-007", user_id, "Network Switches", "Information Technology", 20, 40000.0, "USD", "2026-11-18", "Austin Tech Center", 24, "Net 30", "48-port Layer 3 Gigabit PoE+ enterprise switches", "Completed", "2026-10-14 15:20:00"),
        (8, "PR-2026-008", user_id, "Forklifts & Pallet Jacks", "Material Handling", 4, 60000.0, "USD", "2026-12-10", "Chicago Hub Warehouse", 24, "Net 45", "Electric reach trucks 3,500 lb capacity with lithium batteries", "Analysis In Progress", "2026-10-13 14:00:00"),
        (9, "PR-2026-009", user_id, "Industrial Valves", "Piping & Fluid", 50, 22000.0, "USD", "2026-11-25", "Houston Refinery Hub", 12, "Net 30", "High-pressure stainless steel ball valves Class 600", "Supplier Research", "2026-10-12 10:15:00"),
        (10, "PR-2026-010", user_id, "Precision Calibrators", "Instrumentation", 6, 32000.0, "USD", "2026-12-05", "Denver Research Lab", 24, "Net 30", "Fluke process calibrators with NIST-traceable certificates", "Recommendation Ready", "2026-10-11 16:30:00"),
        (11, "PR-2026-011", user_id, "Packaging Robots", "Automation & Robotics", 2, 110000.0, "USD", "2026-12-20", "Columbus Fulfillment Hub", 36, "Net 45", "Cobot palletizing arm system with safety scanners", "Risk Assessment", "2026-10-10 13:00:00"),
        (12, "PR-2026-012", user_id, "Fire Suppression Systems", "Safety & Compliance", 1, 48000.0, "USD", "2026-11-28", "Atlanta Headquarters", 24, "Net 30", "Clean agent gas extinguishing system for server rooms", "Completed", "2026-10-09 17:00:00"),
    ]

    for r in requests_data:
        cur.execute("""
            INSERT OR REPLACE INTO procurement_requests (id, request_code, user_id, item_name, category, quantity, budget, currency, required_delivery_date, delivery_location, min_warranty_months, payment_terms_pref, additional_requirements, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, r)

    # 4. Insert Quotations for PR-2026-001 through PR-2026-005 matching suppliers count
    # PR-2026-001 has 3 quotes
    # PR-2026-002 has 4 quotes
    # PR-2026-003 has 3 quotes
    # PR-2026-004 has 5 quotes
    # PR-2026-005 has 3 quotes
    quotes_data = [
        # PR-1 (Industrial Transformers - 3 suppliers)
        (1, 1, 1, "Apex Industrial Solutions", "QUO-APX-8821", "Heavy Industrial Step-Down Transformer 500kVA", 16000.0, 5, "USD", 2000.0, 5.0, 3900.0, 2600.0, 2500.0, 0.0, 85000.0, 24, 22, "2026-11-10", "Net 30", "2026-12-01", "quote_apex_industrial.pdf", 96.0, "[]"),
        (2, 1, 2, "Global Electrics & Power", "QUO-GEP-4402", "High-Efficiency 500kVA Transformer Units", 12000.0, 5, "USD", 1500.0, 5.0, 2925.0, 1675.0, 1900.0, 0.0, 63000.0, 36, 18, "2026-11-06", "Net 30", "2026-12-15", "quote_global_electrics.xlsx", 98.0, "[]"),
        (3, 1, 3, "Vanguard Dynamics", "QUO-VNG-1099", "Modular 500kVA Power Transformer Package", 14200.0, 5, "USD", 0.0, 5.0, 3550.0, 2250.0, 2000.0, 0.0, 75000.0, 12, 28, "2026-11-16", "Net 15", "2026-11-30", "quote_vanguard_dynamics.csv", 91.0, "[]"),

        # PR-2 (IT Laptops - 4 suppliers)
        (4, 2, 8, "Summit Tech Hardware", "QUO-STH-7701", "Enterprise Laptops Ultra 7 32GB", 1200.0, 50, "USD", 2000.0, 5.0, 2900.0, 800.0, 500.0, 0.0, 62200.0, 36, 14, "2026-11-02", "Net 30", "2026-12-01", "quote_summit_tech.xlsx", 95.0, "[]"),
        (5, 2, 6, "Pacific Logistics & Components", "QUO-PLC-3312", "Business Notebook Pro 16", 1150.0, 50, "USD", 1500.0, 5.0, 2800.0, 1200.0, 400.0, 0.0, 60400.0, 24, 25, "2026-11-12", "Net 30", "2026-12-01", "quote_pacific_comp.pdf", 90.0, "[]"),
        (6, 2, 7, "Precision Controls Corp", "QUO-PCC-5521", "Rugged Field Laptops Core i7", 1300.0, 50, "USD", 3000.0, 5.0, 3100.0, 900.0, 600.0, 0.0, 66600.0, 36, 16, "2026-11-04", "Net 30", "2026-12-01", "quote_pcc_laptops.pdf", 92.0, "[]"),
        (7, 2, 1, "Apex Industrial Solutions", "QUO-APX-9903", "Corporate Laptop Provisioning Pack", 1280.0, 50, "USD", 2500.0, 5.0, 3075.0, 850.0, 500.0, 0.0, 65925.0, 36, 15, "2026-11-03", "Net 30", "2026-12-01", "quote_apex_laptops.xlsx", 94.0, "[]"),

        # PR-3 (HVAC Systems - 3 suppliers)
        (8, 3, 5, "Nordic Power Systems", "QUO-NPS-2201", "Commercial VRF Heat Pump System 20-ton", 21000.0, 2, "USD", 1000.0, 5.0, 2050.0, 1200.0, 3500.0, 0.0, 47750.0, 36, 21, "2026-11-15", "Net 45", "2026-12-15", "quote_nordic_hvac.pdf", 96.0, "[]"),
        (9, 3, 2, "Global Electrics & Power", "QUO-GEP-9912", "Industrial Chiller & Air Handling Unit", 19500.0, 2, "USD", 800.0, 5.0, 1910.0, 1400.0, 3000.0, 0.0, 44510.0, 24, 18, "2026-11-12", "Net 30", "2026-12-15", "quote_gep_hvac.xlsx", 97.0, "[]"),
        (10, 3, 4, "Titan Heavy Equipment", "QUO-TTN-4421", "Rooftop Packaged HVAC Unit", 18800.0, 2, "USD", 500.0, 5.0, 1855.0, 1600.0, 2800.0, 0.0, 43355.0, 12, 30, "2026-11-24", "Net 30", "2026-12-15", "quote_titan_hvac.csv", 89.0, "[]"),

        # PR-4 (Office Furniture - 5 suppliers)
        (11, 4, 3, "Vanguard Dynamics", "QUO-VNG-7712", "Ergonomic Mesh Chair Set", 260.0, 120, "USD", 1200.0, 5.0, 1500.0, 1400.0, 1800.0, 0.0, 34700.0, 24, 14, "2026-11-20", "Net 30", "2026-12-10", "quote_vanguard_furn.pdf", 93.0, "[]"),
        (12, 4, 8, "Summit Tech Hardware", "QUO-STH-8819", "Motorized Standing Desks Dual Motor", 280.0, 120, "USD", 1500.0, 5.0, 1605.0, 1500.0, 2000.0, 0.0, 37205.0, 36, 16, "2026-11-22", "Net 30", "2026-12-10", "quote_summit_desks.xlsx", 94.0, "[]"),
        (13, 4, 1, "Apex Industrial Solutions", "QUO-APX-3318", "Commercial Office Workstations", 250.0, 120, "USD", 1000.0, 5.0, 1450.0, 1300.0, 1700.0, 0.0, 33450.0, 24, 15, "2026-11-21", "Net 30", "2026-12-10", "quote_apex_furn.pdf", 91.0, "[]"),
        (14, 4, 4, "Titan Heavy Equipment", "QUO-TTN-1102", "Heavy Duty Steel Shelving & Desks", 270.0, 120, "USD", 800.0, 5.0, 1580.0, 1600.0, 1900.0, 0.0, 36680.0, 12, 22, "2026-11-28", "Net 30", "2026-12-10", "quote_titan_desks.csv", 88.0, "[]"),
        (15, 4, 5, "Nordic Power Systems", "QUO-NPS-4491", "Scandinavian Ergonomic Furniture Package", 290.0, 120, "USD", 2000.0, 5.0, 1640.0, 1450.0, 1850.0, 0.0, 37740.0, 36, 18, "2026-11-24", "Net 45", "2026-12-10", "quote_nordic_furn.pdf", 95.0, "[]"),

        # PR-5 (Security Cameras - 3 suppliers)
        (16, 5, 7, "Precision Controls Corp", "QUO-PCC-8822", "4K PoE Vandal-Proof Dome Cameras", 850.0, 30, "USD", 1000.0, 5.0, 1225.0, 600.0, 1200.0, 0.0, 27525.0, 36, 10, "2026-10-22", "Net 30", "2026-11-15", "quote_pcc_cams.pdf", 96.0, "[]"),
        (17, 5, 6, "Pacific Logistics & Components", "QUO-PLC-9918", "NDAA Compliant IP Camera System", 820.0, 30, "USD", 800.0, 5.0, 1190.0, 800.0, 1100.0, 0.0, 26890.0, 24, 18, "2026-10-25", "Net 30", "2026-11-15", "quote_plc_cams.xlsx", 92.0, "[]"),
        (18, 5, 8, "Summit Tech Hardware", "QUO-STH-4410", "Enterprise Surveillance NVR & Camera Bundle", 890.0, 30, "USD", 1200.0, 5.0, 1275.0, 650.0, 1300.0, 0.0, 28725.0, 36, 12, "2026-10-24", "Net 30", "2026-11-15", "quote_sth_cams.pdf", 95.0, "[]"),
    ]

    for q in quotes_data:
        cur.execute("""
            INSERT OR REPLACE INTO quotations (id, request_id, supplier_id, supplier_name, quotation_number, item_description, unit_price, quantity, currency, discount_amount, tax_rate, tax_amount, shipping_cost, installation_cost, other_charges, total_cost, warranty_months, delivery_days, promised_delivery_date, payment_terms, quote_validity_date, filename, extraction_confidence, missing_fields)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, q)

    # 5. Insert Cost Comparisons for PR-2026-001
    cost_data = [
        (1, 1, 1, "Apex Industrial Solutions", 16000.0, 5, 80000.0, 2000.0, 78000.0, 3900.0, 2600.0, 2500.0, 0.0, 85000.0, "USD", 74.1, "Subtotal: 5 x $16,000 = $80,000; Net Subtotal: $80,000 - $2,000 = $78,000; Total = $78,000 + $3,900 (Tax 5%) + $2,600 (Freight) + $2,500 (Installation) = $85,000", "None. All required cost lines documented."),
        (2, 1, 2, "Global Electrics & Power", 12000.0, 5, 60000.0, 1500.0, 58500.0, 2925.0, 1675.0, 1900.0, 0.0, 63000.0, "USD", 100.0, "Subtotal: 5 x $12,000 = $60,000; Net Subtotal: $60,000 - $1,500 = $58,500; Total = $58,500 + $2,925 (Tax 5%) + $1,675 (Freight) + $1,900 (Installation) = $63,000", "None. Complete transparent breakdown verified."),
        (3, 1, 3, "Vanguard Dynamics", 14200.0, 5, 71000.0, 0.0, 71000.0, 3550.0, 2250.0, 2000.0, 0.0, 75000.0, "USD", 84.0, "Subtotal: 5 x $14,200 = $71,000; Net Subtotal: $71,000; Total = $71,000 - $3,800 supplier credit + $3,550 tax + $2,250 freight + $2,000 install = $75,000", "Warranty is at lower boundary (12 mo); Net 15 days payment is shorter than requested Net 30."),
    ]
    for c in cost_data:
        cur.execute("""
            INSERT OR REPLACE INTO cost_comparisons (id, request_id, quotation_id, supplier_name, unit_price, quantity, subtotal, discount_amount, net_subtotal, tax_amount, shipping_cost, installation_cost, other_charges, estimated_total_cost, currency, cost_score, formulas_used, missing_cost_warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    # 6. Insert Risk Assessments for PR-2026-001
    risk_data = [
        (1, 1, 1, "Apex Industrial Solutions", 20.0, "Low Risk", "Low - 22 days delivery (target is 27 days)", "Verified - ISO 9001, UL 1562 listed", "Low - Diversified parts supply chain", "Complete documentation provided", "Standard Net 30", "Strong track record of 97.5% on-time performance", "None", "Standard purchase agreement and milestone acceptance check."),
        (2, 1, 2, "Global Electrics & Power", 14.0, "Low Risk", "Very Low - 18 days delivery (exceeds requirement)", "Verified - CE, IEEE C57, ISO 14001", "Low - Dual manufacturing facilities in EU and US", "Comprehensive test reports and warranty certificate included", "Net 30 with 2% discount for 10-day settlement", "Highest reliability rating (4.6/5.0), 3-year warranty covers all parts and labor", "None", "Lock in 36-month warranty clause in final purchase order contract."),
        (3, 1, 3, "Vanguard Dynamics", 52.0, "Medium Risk", "Moderate Risk - 28 days delivery, exactly 1 day past requested target", "Pending verification on copper winding certifications", "Moderate - Dependent on overseas subcontractor for core coils", "Missing formal warranty SLA sheet", "Net 15 requested instead of Net 30", "Past shipment records show 88% on-time delivery rate", "Detailed QA inspection certificates not attached", "Require Net 30 terms and contractual delay penalty clause before contract execution."),
    ]
    for rsk in risk_data:
        cur.execute("""
            INSERT OR REPLACE INTO risk_assessments (id, request_id, quotation_id, supplier_name, overall_risk_score, risk_category, delivery_risk, compliance_risk, dependency_risk, documentation_risk, commercial_terms_risk, supporting_evidence, missing_evidence, recommended_mitigation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rsk)

    # 7. Insert Recommendations for PR-2026-001
    # Global Electrics & Power is Ranked 1 (Recommended)
    rec_data = [
        (1, 1, 2, "Global Electrics & Power", 1, 1, 94.2, 100.0, 96.0, 86.0, 100.0,
         json.dumps({"cost": 40.0, "delivery": 24.0, "risk": 17.2, "warranty": 15.0}),
         1, "None. Fully satisfies all mandatory criteria.",
         "Best total cost of ownership ($63,000 saves $22,000 vs budget); Reliable delivery timeline (18 days vs 27 days deadline); Lower risk score (14/100, verified tier-1); Strong warranty and support (36 months exceeds 24 month minimum).",
         "Lead time requires order confirmation within 15 days to lock in production schedule.",
         "Global Electrics & Power is the clear standout recommendation. At $63,000 total landed cost, they are $22,000 under budget and $12,000 cheaper than Vanguard Dynamics while delivering superior build quality, 36-month comprehensive warranty, and earliest delivery date (18 days).",
         "Request free factory testing and extend payment terms from Net 30 to Net 45 given high order volume."),
        (2, 1, 1, "Apex Industrial Solutions", 2, 0, 81.5, 74.1, 90.0, 80.0, 85.0,
         json.dumps({"cost": 29.6, "delivery": 22.5, "risk": 16.0, "warranty": 12.8}),
         1, "None. Satisfies mandatory requirements.",
         "Reputable US supplier with established local inventory; Comprehensive UL certification; 24-month warranty matches requirements.",
         "Total landed cost is $85,000 ($22,000 higher than Supplier B); Higher shipping costs ($2,600).",
         "Apex Industrial is a reliable fallback option with high compliance scores, but carries a 35% cost premium over Global Electrics.",
         "Counter-offer with $72,000 matching competitive quote levels and ask to waive installation fees."),
        (3, 1, 3, "Vanguard Dynamics", 3, 0, 68.2, 84.0, 72.0, 48.0, 50.0,
         json.dumps({"cost": 33.6, "delivery": 18.0, "risk": 9.6, "warranty": 7.5}),
         0, "Delivery commitment (28 days) breaches the required delivery deadline (27 days); Warranty (12 months) fails to meet mandatory minimum (24 months).",
         "Competitive unit pricing ($75,000 total landed cost); Modular design allows easier maintenance.",
         "Delivery deadline exceeded by 1 day; Warranty is half the required minimum (12 mo vs 24 mo); Payment terms (Net 15) are restrictive; Medium risk assessment.",
         "Vanguard Dynamics cannot be recommended in its current form due to mandatory constraint breaches (insufficient warranty duration and delivery timeline overrun).",
         "If negotiating, insist on 24-month warranty matching RFP specifications and Net 30 payment terms without price increase.")
    ]
    for rec in rec_data:
        cur.execute("""
            INSERT OR REPLACE INTO recommendations (id, request_id, quotation_id, supplier_name, rank, is_recommended, overall_score, cost_score, delivery_score, risk_score, warranty_score, weight_breakdown, satisfies_mandatory, disqualification_reasons, key_advantages, main_disadvantages, explanation, negotiation_tips)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rec)

    # 8. Insert Agent Workflow Run for PR-2026-001
    cur.execute("""
        INSERT OR REPLACE INTO agent_runs (id, request_id, status, execution_mode, started_at, completed_at, total_duration_seconds, error_message)
        VALUES (1, 1, 'Completed', 'DEMO_FALLBACK', '2026-10-19 14:15:00', '2026-10-19 14:15:04', 4.25, NULL)
    """)

    agent_outputs_data = [
        (1, 1, 1, 1, "Requirement Parser Agent", "Convert procurement requests into structured evaluation criteria", "Completed",
         "Request PR-2026-001: 5 Industrial Transformers, $100k budget, 27 days deadline, 24-mo warranty",
         "Parsed 4 mandatory constraints (budget <= $100,000, qty == 5, delivery <= 27 days, warranty >= 24 mo) and 2 preferred preferences (Net 30, copper windings).",
         json.dumps({"mandatory": ["budget_max_100k", "qty_5", "delivery_27_days", "warranty_min_24_mo"], "preferences": ["payment_net_30", "copper_windings"], "confidence": 0.99}),
         0.65, "None", "RFP-2026-001 specification sheet"),
        (2, 1, 1, 2, "Quote Analyzer Agent", "Extract and normalize supplier quotation information", "Completed",
         "3 documents: PDF (Apex), XLSX (Global Electrics), CSV (Vanguard Dynamics)",
         "Extracted and normalized 3 supplier quotations with 100% data coverage; identified missing warranty sheet on Quote 3.",
         json.dumps({"quotes_parsed": 3, "avg_confidence": 0.95, "missing_fields": ["Quote 3: detailed warranty certificate"]}),
         0.92, "Quote 3: Payment term Net 15 flagged as tighter than requested Net 30", "Upload hashes: sha256_apx, sha256_gep, sha256_vng"),
        (3, 1, 1, 3, "Supplier Researcher Agent", "Gather supplier information from verified databases", "Completed",
         "3 Suppliers: Apex Industrial Solutions, Global Electrics & Power, Vanguard Dynamics",
         "Retrieved historical reliability records: Apex (97.5% on-time, Tier 1), Global Electrics (96.0% on-time, Tier 1), Vanguard (88.0% on-time, Tier 2).",
         json.dumps({"sources": ["ERP Supplier Registry", "Dun & Bradstreet Benchmarks", "Historical PO Ledger"], "coverage": "100%"}),
         0.78, "None", "ERP Vendor ID: V-101, V-204, V-509"),
        (4, 1, 1, 4, "Risk Assessor Agent", "Evaluate supplier risks across delivery, compliance, and terms", "Completed",
         "Extracted quotes and supplier performance evidence",
         "Assessed risk categories: Global Electrics (14/100, Low), Apex (20/100, Low), Vanguard (52/100, Medium due to delivery slip and warranty gap).",
         json.dumps({"low_risk_count": 2, "medium_risk_count": 1, "high_risk_count": 0}),
         0.68, "Vanguard Dynamics delivery risk flagged (promised 28 days vs 27 days allowed)", "Supplier compliance database v2026.1"),
        (5, 1, 1, 5, "Cost Optimizer Agent", "Calculate and compare total procurement ownership costs", "Completed",
         "3 Quotation financial lines: Unit prices, discounts, freight, tax, and installation",
         "Calculated total landed costs: Global Electrics ($63,000, Best), Vanguard ($75,000), Apex ($85,000). Identified $22,000 cost savings under budget.",
         json.dumps({"lowest_cost": 63000.0, "max_cost": 85000.0, "savings_vs_budget": 37000.0}),
         0.54, "None. All calculation equations verified deterministically without assumptions.", "Formula: Net_Subtotal + Tax + Freight + Install"),
        (6, 1, 1, 6, "Procurement Advisor Agent", "Generate ranked vendor shortlist and explainable recommendations", "Completed",
         "Synthesized criteria from all 5 preceding agents",
         "Ranked Global Electrics & Power #1 (Score 94.2/100, Recommended). Vanguard disqualified from primary recommendation due to warranty/delivery breaches.",
         json.dumps({"ranked_list": ["Global Electrics & Power", "Apex Industrial Solutions", "Vanguard Dynamics (Disqualified)"], "recommended": "Global Electrics & Power"}),
         0.68, "Vanguard Dynamics failed mandatory warranty constraint (12 months provided vs 24 months requested)", "Scoring model weights: Cost 40%, Deliv 25%, Risk 20%, Warr 15%")
    ]

    for ao in agent_outputs_data:
        cur.execute("""
            INSERT OR REPLACE INTO agent_outputs (id, run_id, request_id, agent_number, agent_name, purpose, status, input_summary, output_summary, full_output_json, execution_duration_seconds, warnings, evidence_references)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ao)

    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic enterprise procurement data!")

if __name__ == '__main__':
    seed_database(force=True)

"""
AGENT 5: COST OPTIMIZER AGENT
Calculates deterministic total procurement landed costs, breaks down financial components,
analyzes budget feasibility, and delivers transparent cost optimization analytics.
"""

import time
from datetime import datetime
from services.cost_calculator import calculate_quotation_cost

class CostOptimizerAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Cost Optimizer Agent"
        self.agent_number = 5
        self.purpose = "Calculate and compare total procurement ownership costs"

    def execute(self, normalized_quotes, request_requirements):
        start_ts = datetime.now()
        start_time = time.time()
        
        budget = float(request_requirements.get('budget', 0.0))
        currency = request_requirements.get('currency', 'USD')
        req_code = request_requirements.get('request_code', 'REQ')
        
        cost_comparisons = []
        cost_breakdown_table = []
        warnings = []
        over_budget_suppliers = []

        for q in normalized_quotes:
            c_res = calculate_quotation_cost(
                unit_price=q.get('unit_price', 0.0),
                quantity=q.get('quantity', 1),
                discount_amount=q.get('discount_amount', 0.0),
                tax_rate=q.get('tax_rate', 0.0),
                tax_amount=q.get('tax_amount'),
                shipping_cost=q.get('shipping_cost', 0.0),
                installation_cost=q.get('installation_cost', 0.0),
                other_charges=q.get('other_charges', 0.0),
                currency=currency
            )

            tot = c_res['estimated_total_cost']
            s_name = q.get('supplier_name', 'Unknown')
            budget_diff = round(budget - tot, 2)
            
            if budget > 0 and tot > budget:
                overrun = tot - budget
                over_budget_suppliers.append(s_name)
                warnings.append(
                    f"{s_name}: Landed cost ({currency} {tot:,.2f}) exceeds budget cap ({currency} {budget:,.2f}) by {currency} {overrun:,.2f}"
                )

            cost_comparisons.append({
                "quotation_id": q.get('id'),
                "supplier_name": s_name,
                "unit_price": c_res['unit_price'],
                "quantity": c_res['quantity'],
                "subtotal": c_res['subtotal'],
                "discount_amount": c_res['discount_amount'],
                "net_subtotal": c_res['net_subtotal'],
                "tax_rate": c_res['tax_rate'],
                "tax_amount": c_res['tax_amount'],
                "shipping_cost": c_res['shipping_cost'],
                "installation_cost": c_res['installation_cost'],
                "other_charges": c_res['other_charges'],
                "estimated_total_cost": tot,
                "budget_difference": budget_diff,
                "currency": currency,
                "formulas_used": c_res['formulas_used'],
                "missing_cost_warnings": c_res['missing_cost_warnings']
            })

            # Format for table display
            cost_breakdown_table.append({
                "supplier_name": s_name,
                "gross_subtotal": f"{currency} {c_res['subtotal']:,.2f}",
                "discount": f"{currency} {c_res['discount_amount']:,.2f}" if c_res['discount_amount'] > 0 else "—",
                "net_subtotal": f"{currency} {c_res['net_subtotal']:,.2f}",
                "tax": f"{currency} {c_res['tax_amount']:,.2f}" if c_res['tax_amount'] > 0 else "0.00",
                "shipping": f"{currency} {c_res['shipping_cost']:,.2f}" if c_res['shipping_cost'] > 0 else "Included",
                "installation": f"{currency} {c_res['installation_cost']:,.2f}" if c_res['installation_cost'] > 0 else "N/A",
                "other_charges": f"{currency} {c_res['other_charges']:,.2f}" if c_res['other_charges'] > 0 else "0.00",
                "estimated_total": f"{currency} {tot:,.2f}",
                "estimated_total_num": tot,
                "budget_difference": f"{'+' if budget_diff >= 0 else ''}{currency} {budget_diff:,.2f} ({'Under' if budget_diff >= 0 else 'Over'})",
                "is_within_budget": budget_diff >= 0,
                "currency": currency
            })

        # Calculate comparative metrics
        costs = [c['estimated_total_cost'] for c in cost_comparisons if c['estimated_total_cost'] > 0]
        min_cost = min(costs) if costs else 0.0
        max_cost = max(costs) if costs else 0.0
        cost_spread = round(max_cost - min_cost, 2)
        
        # Sort costs to find second lowest
        sorted_costs = sorted(cost_comparisons, key=lambda x: x['estimated_total_cost'])
        cheapest_supplier = sorted_costs[0]['supplier_name'] if sorted_costs else "None"
        second_cheapest = sorted_costs[1] if len(sorted_costs) > 1 else None
        diff_from_second = round(second_cheapest['estimated_total_cost'] - min_cost, 2) if second_cheapest else 0.0

        for c in cost_comparisons:
            tot = c['estimated_total_cost']
            c['diff_from_lowest'] = round(tot - min_cost, 2)
            c['pct_diff_from_lowest'] = round(((tot - min_cost) / min_cost * 100.0), 1) if min_cost > 0 else 0.0
            c['is_lowest_cost'] = (tot == min_cost)

        # Natural-language cost explanation in paragraphs
        p1 = (
            f"The Cost Optimizer Agent computed landed procurement totals for {len(cost_comparisons)} supplier bid(s) using "
            f"standardized deterministic financial logic (Gross Subtotal = Unit Price x Quantity; Net Subtotal = Subtotal - Discount; "
            f"Estimated Landed Total = Net Subtotal + Taxes + Shipping + Installation + Ancillary Fees). "
            f"No arbitrary machine learning adjustments or speculative assumptions were applied to monetary values."
        )
        p2 = (
            f"Across all proposals, estimated landed costs range from {currency} {min_cost:,.2f} to {currency} {max_cost:,.2f}, "
            f"yielding an overall cost spread of {currency} {cost_spread:,.2f}. The lowest calculated landed cost is offered by "
            f"'{cheapest_supplier}' at {currency} {min_cost:,.2f}, which is {currency} {diff_from_second:,.2f} "
            f"({round(diff_from_second / min_cost * 100, 1) if min_cost > 0 else 0}%) lower than the runner-up "
            f"'{second_cheapest['supplier_name'] if second_cheapest else 'N/A'}'."
        )
        p3 = (
            f"In benchmarking against the allocated budgetary cap of {currency} {budget:,.2f}, "
            + (f"{len(cost_comparisons) - len(over_budget_suppliers)} of {len(cost_comparisons)} supplier(s) comply with budget constraints. "
               f"However, {len(over_budget_suppliers)} supplier(s) ({', '.join(over_budget_suppliers)}) exceed the authorized ceiling and "
               f"will require formal budget extension approval or commercial renegotiation." if over_budget_suppliers else
               f"all evaluated quotations fall comfortably within the authorized budgetary allocation.")
        )
        explanation_paragraphs = [p1, p2, p3]

        # Optimization Insights bullet points
        key_findings = [
            f"Lowest Calculated Landed Total: {currency} {min_cost:,.2f} offered by '{cheapest_supplier}'.",
            f"Variance from Next Supplier: '{cheapest_supplier}' provides a {currency} {diff_from_second:,.2f} cost advantage over the next lowest bidder.",
            f"Budget Compliance: {len(cost_comparisons) - len(over_budget_suppliers)} of {len(cost_comparisons)} suppliers within budget of {currency} {budget:,.2f}.",
            f"Budget Overruns: {', '.join(over_budget_suppliers)} exceed budget cap." if over_budget_suppliers else "No Budget Deficits: All bids satisfy budgetary limits.",
            f"Cost Driver Analysis: Base product net subtotal represents the majority of total expenditure; shipping and taxes contribute secondary variances.",
            f"Negotiation Opportunity: For higher-ranked suppliers, benchmark against {currency} {min_cost:,.2f} to request targeted price matching."
        ]

        # Visualization 1: Supplier Cost Comparison Bar Chart
        chart_data_total = {
            "labels": [c['supplier_name'] for c in cost_comparisons],
            "datasets": [
                {
                    "label": f"Estimated Total Landed Cost ({currency})",
                    "data": [c['estimated_total_cost'] for c in cost_comparisons],
                    "backgroundColor": [
                        "rgba(32, 167, 122, 0.75)" if c['is_lowest_cost'] else
                        ("rgba(224, 36, 36, 0.75)" if c['estimated_total_cost'] > budget else "rgba(79, 131, 255, 0.75)")
                        for c in cost_comparisons
                    ],
                    "borderColor": [
                        "#20A77A" if c['is_lowest_cost'] else
                        ("#E02424" if c['estimated_total_cost'] > budget else "#4F83FF")
                        for c in cost_comparisons
                    ],
                    "borderWidth": 1.5,
                    "borderRadius": 6
                }
            ]
        }

        # Visualization 2: Cost Component Breakdown (Stacked Bar Chart: Net Subtotal, Tax, Shipping, Installation, Other)
        chart_data_components = {
            "labels": [c['supplier_name'] for c in cost_comparisons],
            "datasets": [
                {
                    "label": "Product Net Subtotal",
                    "data": [c['net_subtotal'] for c in cost_comparisons],
                    "backgroundColor": "rgba(79, 131, 255, 0.8)",
                    "stack": "cost_components"
                },
                {
                    "label": "Taxes & Duties",
                    "data": [c['tax_amount'] for c in cost_comparisons],
                    "backgroundColor": "rgba(255, 193, 7, 0.8)",
                    "stack": "cost_components"
                },
                {
                    "label": "Freight & Shipping",
                    "data": [c['shipping_cost'] for c in cost_comparisons],
                    "backgroundColor": "rgba(255, 152, 102, 0.8)",
                    "stack": "cost_components"
                },
                {
                    "label": "Installation Charges",
                    "data": [c['installation_cost'] for c in cost_comparisons],
                    "backgroundColor": "rgba(146, 116, 248, 0.8)",
                    "stack": "cost_components"
                },
                {
                    "label": "Ancillary Fees",
                    "data": [c['other_charges'] for c in cost_comparisons],
                    "backgroundColor": "rgba(100, 116, 139, 0.8)",
                    "stack": "cost_components"
                }
            ]
        }

        # Visualization 3: Budget Comparison (Supplier Total vs Budget Ceiling)
        chart_data_budget = {
            "labels": [c['supplier_name'] for c in cost_comparisons],
            "datasets": [
                {
                    "label": f"Quoted Landed Cost ({currency})",
                    "data": [c['estimated_total_cost'] for c in cost_comparisons],
                    "backgroundColor": "rgba(79, 131, 255, 0.75)",
                    "borderColor": "#4F83FF",
                    "borderWidth": 1.5,
                    "borderRadius": 6
                },
                {
                    "label": f"Budget Ceiling Cap ({currency})",
                    "data": [budget] * len(cost_comparisons),
                    "type": "line",
                    "borderColor": "#E02424",
                    "borderWidth": 2.5,
                    "borderDash": [6, 4],
                    "pointRadius": 4,
                    "fill": False
                }
            ]
        }

        # Enrich with Google Gemini (Graphs & Landed Cost Analytics)
        ai_engine = "Deterministic Offline Engine"
        ai_status = "Local Deterministic Processing"
        try:
            from services.gemini_service import enrich_step5_with_gemini, get_gemini_api_key
            g_key = get_gemini_api_key()
            if g_key:
                g_res = enrich_step5_with_gemini(normalized_quotes, parsed_reqs, cost_comparisons, api_key=g_key)
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
            from services.matter_service import generate_step5_matter_ngrok, get_ngrok_api_key
            n_key = get_ngrok_api_key()
            if n_key:
                n_res = generate_step5_matter_ngrok(normalized_quotes, parsed_reqs, cost_comparisons, api_key=n_key)
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
            "quotations_calculated": len(cost_comparisons),
            "lowest_cost": min_cost,
            "cheapest_supplier": cheapest_supplier,
            "cost_spread": cost_spread,
            "budget_cap": budget,
            "over_budget_count": len(over_budget_suppliers),
            "currency": currency,
            "started_at": start_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": end_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration
        }

        output_summary = (
            f"Calculated landed ownership costs across {len(cost_comparisons)} supplier(s). "
            f"Lowest total: {currency} {min_cost:,.2f} ({cheapest_supplier}); "
            f"Cost spread: {currency} {cost_spread:,.2f}. Budget compliance: "
            f"{len(cost_comparisons) - len(over_budget_suppliers)}/{len(cost_comparisons)} eligible."
        )

        return {
            "agent_number": self.agent_number,
            "agent_name": self.name,
            "purpose": self.purpose,
            "status": "Completed",
            "ai_engine": ai_engine,
            "ai_status": ai_status,
            "input_summary": f"Calculated deterministic line-item landed totals for {len(normalized_quotes)} supplier quotes",
            "output_summary": output_summary,
            "execution_summary": execution_summary,
            "explanation_paragraphs": explanation_paragraphs,
            "key_findings": key_findings,
            "cost_comparisons": cost_comparisons,
            "cost_breakdown_table": cost_breakdown_table,
            "chart_data_total": chart_data_total,
            "chart_data_components": chart_data_components,
            "chart_data_budget": chart_data_budget,
            "lowest_cost": min_cost,
            "cheapest_supplier": cheapest_supplier,
            "cost_spread": cost_spread,
            "warnings": warnings,
            "evidence_references": "Standardized Landed Cost Formula: Net_Subtotal + Tax + Shipping + Installation + Other",
            "execution_duration_seconds": duration
        }

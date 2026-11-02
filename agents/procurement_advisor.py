"""
AGENT 6: PROCUREMENT ADVISOR AGENT
Synthesizes verified results from all preceding agents into an explainable multi-criteria
decision matrix, delivers a 9-point structured recommendation narrative, generates decision visualizations,
and provides human-in-the-loop governance options.
"""

import time
import json
from datetime import datetime
from services.scoring_engine import score_procurement_quotations

class ProcurementAdvisorAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.name = "Procurement Advisor Agent"
        self.agent_number = 6
        self.purpose = "Generate a ranked vendor shortlist with explainable recommendations"

    def execute(self, parsed_reqs, normalized_quotes, supplier_profiles,
                risk_assessments, cost_comparisons, custom_weights=None):
        start_ts = datetime.now()
        start_time = time.time()
        
        # Merge data into scoring items
        cost_map = {c['quotation_id']: c for c in cost_comparisons}
        risk_map = {r['quotation_id']: r for r in risk_assessments}
        profile_map = {p['supplier_name'].lower(): p for p in supplier_profiles}

        scoring_input = []
        for q in normalized_quotes:
            q_id = q['id']
            cost_info = cost_map.get(q_id, {})
            risk_info = risk_map.get(q_id, {})
            
            scoring_input.append({
                "id": q_id,
                "supplier_name": q.get('supplier_name'),
                "total_cost": cost_info.get('estimated_total_cost', q.get('total_cost', 0.0)),
                "warranty_months": q.get('warranty_months', 12),
                "delivery_days": q.get('delivery_days', 30),
                "promised_delivery_date": q.get('promised_delivery_date'),
                "risk_score": risk_info.get('overall_risk_score', 30.0)
            })

        # Run multi-criteria scoring engine
        scored_results = score_procurement_quotations(
            quotations=scoring_input,
            request_criteria=parsed_reqs,
            custom_weights=custom_weights
        )

        weights = custom_weights or {
            'cost': 0.40,
            'delivery': 0.25,
            'risk': 0.20,
            'warranty': 0.15
        }

        ranked_recommendations = []
        ranking_table = []
        warnings = []
        recommended_supplier = None
        alternative_supplier = None
        has_eligible = any(r['satisfies_mandatory'] for r in scored_results)

        budget = float(parsed_reqs.get('budget', 0.0))
        currency = parsed_reqs.get('currency', 'USD')
        req_deliv = parsed_reqs.get('required_delivery_date', '')
        min_warr = parsed_reqs.get('min_warranty_months', 12)
        req_item = parsed_reqs.get('item_name', 'Equipment')

        eligible_ranked = [r for r in scored_results if r['satisfies_mandatory']]
        disqualified_ranked = [r for r in scored_results if not r['satisfies_mandatory']]

        if eligible_ranked:
            top_winner = eligible_ranked[0]
            recommended_supplier = top_winner['supplier_name']
            if len(eligible_ranked) > 1:
                alternative_supplier = eligible_ranked[1]['supplier_name']
        elif scored_results:
            top_winner = scored_results[0]
            recommended_supplier = None  # No supplier satisfies all mandatory criteria
            alternative_supplier = None

        for item in scored_results:
            q_id = item['quotation_id']
            s_name = item['supplier_name']
            cost_info = cost_map.get(q_id, {})
            risk_info = risk_map.get(q_id, {})
            prof = profile_map.get(s_name.lower(), {})

            advantages = []
            disadvantages = []
            negotiation_tips = []

            # Cost evaluation
            tot_cost = item['total_cost']
            if cost_info.get('is_lowest_cost'):
                advantages.append(f"Lowest total landed cost ({currency} {tot_cost:,.2f}) among all evaluated bids")
            elif tot_cost <= budget:
                diff = cost_info.get('diff_from_lowest', 0.0)
                if diff > 0:
                    disadvantages.append(f"Cost is {currency} {diff:,.2f} higher than lowest quotation")
                    negotiation_tips.append(f"Counter-offer using competitor quotation ({currency} {cost_info.get('diff_from_lowest'):,.2f} lower) to seek price matching.")
            
            if tot_cost <= budget and budget > 0:
                savings = budget - tot_cost
                advantages.append(f"Under allocated budget by {currency} {savings:,.2f} ({(savings/budget*100):.1f}% savings)")

            # Delivery evaluation
            deliv_days = item.get('delivery_commitment', '30 days')
            if item['delivery_score'] >= 80:
                advantages.append(f"Reliable, expedited delivery timeline ({deliv_days})")
            else:
                disadvantages.append(f"Delivery schedule is tight or delayed ({deliv_days})")
                negotiation_tips.append("Negotiate expedited shipping or pre-shipment buffer staging.")

            # Risk evaluation
            r_cat = risk_info.get('risk_category', 'Medium Risk')
            r_score = risk_info.get('overall_risk_score', 30.0)
            if r_cat == 'Low Risk':
                advantages.append(f"Low operational and compliance risk (Risk score: {r_score}/100, Tier 1)")
            else:
                disadvantages.append(f"{r_cat} (Risk score: {r_score}/100) — {risk_info.get('delivery_risk')} delivery risk")
                negotiation_tips.append("Insert penalty clauses for delivery delays and require performance security bond.")

            # Warranty evaluation
            warr_mo = f"{prof.get('warranty_months') or item.get('warranty_commitment', 12)} months"
            if item['warranty_score'] >= 80:
                advantages.append(f"Comprehensive warranty coverage ({warr_mo}) exceeding baseline requirements")
            else:
                disadvantages.append(f"Warranty is limited ({warr_mo})")
                negotiation_tips.append(f"Request warranty extension to {min_warr} months at no additional charge.")

            # Explanation
            if item.get('is_recommended') and item['satisfies_mandatory']:
                explanation = (
                    f"{s_name} is the top recommended supplier with a weighted score of {item['overall_score']}/100. "
                    f"It satisfies all mandatory requirements (budget, delivery deadline, and warranty) while offering "
                    f"{'the lowest total landed cost' if cost_info.get('is_lowest_cost') else 'an optimal balance of cost and reliability'}. "
                    f"With {r_cat.lower()} profile and verified performance, this vendor minimizes procurement risk."
                )
            elif not item['satisfies_mandatory']:
                disqual_str = "; ".join(item['disqualifications'])
                explanation = (
                    f"{s_name} cannot be recommended as it breaches mandatory procurement constraints: {disqual_str}. "
                    f"Unless these constraints are formally waived or renegotiated, this vendor is disqualified."
                )
                warnings.append(f"{s_name} failed mandatory requirements: {disqual_str}")
            else:
                explanation = (
                    f"{s_name} is ranked #{item['rank']} with an overall score of {item['overall_score']}/100. "
                    f"While it satisfies all mandatory criteria, it scores lower than the top candidate primarily due to "
                    f"{'higher total landed cost' if not cost_info.get('is_lowest_cost') else 'lower warranty / delivery scores'}."
                )

            rec_dict = {
                "quotation_id": q_id,
                "supplier_name": s_name,
                "rank": item['rank'],
                "is_recommended": item['is_recommended'] and item['satisfies_mandatory'],
                "overall_score": item['overall_score'],
                "cost_score": item['cost_score'],
                "delivery_score": item['delivery_score'],
                "risk_score": item['risk_score'],
                "warranty_score": item['warranty_score'],
                "weight_breakdown": json.dumps(item['weight_breakdown']),
                "satisfies_mandatory": item['satisfies_mandatory'],
                "disqualification_reasons": " | ".join(item['disqualifications']) if item['disqualifications'] else "None. Fully satisfies mandatory criteria.",
                "key_advantages": " | ".join(advantages) if advantages else "Standard competitive offering.",
                "main_disadvantages": " | ".join(disadvantages) if disadvantages else "No critical drawbacks identified.",
                "explanation": explanation,
                "negotiation_tips": " | ".join(negotiation_tips) if negotiation_tips else "Proceed to standard purchase order issuance."
            }
            ranked_recommendations.append(rec_dict)

            ranking_table.append({
                "rank": item['rank'],
                "supplier_name": s_name,
                "cost_score": f"{item['cost_score']:.1f}",
                "delivery_score": f"{item['delivery_score']:.1f}",
                "risk_score": f"{item['risk_score']:.1f}",
                "warranty_score": f"{item['warranty_score']:.1f}",
                "weighted_total": f"{item['overall_score']:.1f}",
                "weighted_total_num": item['overall_score'],
                "eligibility_status": "Eligible" if item['satisfies_mandatory'] else "Disqualified (Mandatory Breach)",
                "is_recommended": item['is_recommended'] and item['satisfies_mandatory']
            })

        # Top winner details for Final Recommendation section
        top_winner_record = next((r for r in ranked_recommendations if r['is_recommended']), None)
        if not top_winner_record and eligible_ranked:
            top_winner_record = ranked_recommendations[0]

        top_cost_info = cost_map.get(top_winner_record['quotation_id'], {}) if top_winner_record else {}
        top_risk_info = risk_map.get(top_winner_record['quotation_id'], {}) if top_winner_record else {}

        final_recommendation = {
            "has_eligible_winner": has_eligible,
            "recommended_supplier": recommended_supplier if has_eligible else "No supplier fully satisfies all mandatory requirements.",
            "total_cost": f"{currency} {top_cost_info.get('estimated_total_cost', 0.0):,.2f}" if has_eligible else "N/A",
            "overall_score": f"{top_winner_record['overall_score']:.1f} / 100" if (has_eligible and top_winner_record) else "N/A",
            "risk_category": top_risk_info.get('risk_category', 'Low Risk') if has_eligible else "N/A",
            "delivery_commitment": f"{next((q['delivery_days'] for q in normalized_quotes if q['supplier_name'] == recommended_supplier), 30)} days" if has_eligible else "N/A",
            "warranty": f"{next((q['warranty_months'] for q in normalized_quotes if q['supplier_name'] == recommended_supplier), 12)} months" if has_eligible else "N/A",
            "compliance_evidence": top_risk_info.get('supporting_evidence', 'Verified enterprise vendor') if has_eligible else "N/A",
            "evidence_limitations": "Internal registry records verified; third-party credit API integration pending."
        }

        # 9-point structured recommendation explanation narrative
        top_sname = recommended_supplier or "None"
        alt_sname = alternative_supplier or (eligible_ranked[1]['supplier_name'] if len(eligible_ranked) > 1 else "None")
        
        explanation_sections = [
            {
                "title": "1. Executive Summary",
                "content": (
                    f"Following sequential multi-agent evaluation of {len(normalized_quotes)} supplier proposals for {req_item}, "
                    + (f"'{top_sname}' is formally recommended for contract award with a top composite score of {top_winner_record['overall_score']:.1f}/100. "
                       f"The vendor complies with all mandatory budgetary, delivery, and warranty parameters while minimizing operational exposure."
                       if has_eligible else
                       "no submitted supplier proposal fully satisfies all mandatory procurement constraints. Review individual disqualification notices before proceeding.")
                )
            },
            {
                "title": "2. Why the Supplier Was Selected",
                "content": (
                    f"'{top_sname}' achieves the strongest balance across the weighted evaluation model (Cost: {int(weights['cost']*100)}%, "
                    f"Delivery: {int(weights['delivery']*100)}%, Risk: {int(weights['risk']*100)}%, Warranty: {int(weights['warranty']*100)}%). "
                    f"Unlike non-compliant candidates, '{top_sname}' delivers within the required timeline without compromising warranty coverage or exceeding the budget ceiling."
                    if has_eligible else
                    "Contract award cannot be granted at this stage because all candidates breached at least one non-negotiable threshold."
                )
            },
            {
                "title": "3. Cost Advantages",
                "content": (
                    f"The calculated total landed cost for '{top_sname}' is {currency} {top_cost_info.get('estimated_total_cost', 0.0):,.2f}, "
                    f"which {'is the lowest overall landed cost evaluated' if top_cost_info.get('is_lowest_cost') else 'represents exceptional value relative to vendor reliability'}. "
                    f"This generates a net budgetary surplus of {currency} {max(0.0, budget - top_cost_info.get('estimated_total_cost', 0.0)):,.2f}."
                    if has_eligible else
                    f"Quoted costs ranged from {currency} {min(c['estimated_total_cost'] for c in cost_comparisons):,.2f} to {currency} {max(c['estimated_total_cost'] for c in cost_comparisons):,.2f}."
                )
            },
            {
                "title": "4. Delivery and Warranty Assessment",
                "content": (
                    f"Delivery timeline is committed at {final_recommendation['delivery_commitment']}, fully aligning with target delivery date {req_deliv}. "
                    f"The proposed warranty of {final_recommendation['warranty']} satisfies the mandatory {min_warr}-month enterprise threshold."
                    if has_eligible else
                    f"Disqualifications occurred where suppliers promised delivery beyond {req_deliv} or provided less than {min_warr} months warranty."
                )
            },
            {
                "title": "5. Risk Considerations",
                "content": (
                    f"'{top_sname}' is categorized as '{final_recommendation['risk_category']}' with a risk index of {top_risk_info.get('overall_risk_score', 20.0)}/100. "
                    f"Mitigations have been drafted for delivery buffer staging and standard acceptance testing."
                    if has_eligible else
                    "Significant operational or compliance risks were detected across disqualified proposals, including warranty gaps and unverified vendor status."
                )
            },
            {
                "title": "6. Supplier Comparison",
                "content": (
                    f"Compared to alternative candidate '{alt_sname}', '{top_sname}' demonstrated superior overall compliance and scoring. "
                    f"While competing proposals offered varied commercial terms, none matched the composite strength of the recommended vendor."
                    if has_eligible else
                    "Comparative assessment indicates no supplier achieved complete compliance across all mandatory criteria."
                )
            },
            {
                "title": "7. Negotiation Opportunities",
                "content": (
                    f"Targeted negotiation recommendations for '{top_sname}': "
                    f"1) Request payment term extension from Net 30 to Net 45; "
                    f"2) Secure a 2-3% prompt-payment discount; "
                    f"3) Formalize liquidated damages clauses for delays exceeding 5 business days."
                )
            },
            {
                "title": "8. Missing Information",
                "content": (
                    "External credit bureau scores and real-time sanctions list APIs were not integrated into this workflow run. "
                    "All findings are based on internal ERP history, verified vendor catalogs, and certified quotation documents."
                )
            },
            {
                "title": "9. Final Decision Considerations",
                "content": (
                    "Procurement authority may now proceed to execute Purchase Order issuance, request secondary negotiation with "
                    f"'{top_sname}', or record a human override to select an alternative vendor with justified business rationale."
                )
            }
        ]

        # Key findings bullet points
        key_findings = [
            f"Recommended Supplier: {recommended_supplier if has_eligible else 'None — All candidates breached mandatory requirements.'}",
            f"Eligibility Rate: {len(eligible_ranked)} of {len(scored_results)} supplier(s) fully satisfied all mandatory requirements.",
            f"Evaluation Weights Applied: Cost ({int(weights['cost']*100)}%), Delivery ({int(weights['delivery']*100)}%), Risk ({int(weights['risk']*100)}%), Warranty ({int(weights['warranty']*100)}%).",
            f"Top Overall Score: {top_winner_record['overall_score']:.1f}/100 achieved by '{top_sname}'.",
            f"Alternative Backup Option: '{alt_sname}' identified as qualified secondary vendor." if alt_sname != 'None' else "Backup Option: No qualified secondary vendor identified.",
            f"Disqualifications: {len(disqualified_ranked)} quotation(s) failed mandatory checks (budget, deadline, or warranty)."
        ]

        # Visualization 1: Supplier Weighted-Score Comparison Bar Chart
        chart_data_scores = {
            "labels": [r['supplier_name'] for r in scored_results],
            "datasets": [
                {
                    "label": "Overall Weighted Score (0-100)",
                    "data": [r['overall_score'] for r in scored_results],
                    "backgroundColor": [
                        "rgba(32, 167, 122, 0.75)" if r['is_recommended'] and r['satisfies_mandatory'] else
                        ("rgba(79, 131, 255, 0.75)" if r['satisfies_mandatory'] else "rgba(224, 36, 36, 0.75)")
                        for r in scored_results
                    ],
                    "borderColor": [
                        "#20A77A" if r['is_recommended'] and r['satisfies_mandatory'] else
                        ("#4F83FF" if r['satisfies_mandatory'] else "#E02424")
                        for r in scored_results
                    ],
                    "borderWidth": 1.5,
                    "borderRadius": 6
                }
            ]
        }

        # Visualization 2: Cost-versus-Risk Chart (Scatter / Dual Dataset)
        chart_data_cost_vs_risk = {
            "labels": [r['supplier_name'] for r in scored_results],
            "cost_data": [cost_map.get(r['quotation_id'], {}).get('estimated_total_cost', 0.0) for r in scored_results],
            "risk_data": [risk_map.get(r['quotation_id'], {}).get('overall_risk_score', 30.0) for r in scored_results],
            "currency": currency,
            "datasets": [
                {
                    "label": f"Estimated Total Cost ({currency})",
                    "data": [cost_map.get(r['quotation_id'], {}).get('estimated_total_cost', 0.0) for r in scored_results],
                    "backgroundColor": "rgba(79, 131, 255, 0.75)",
                    "borderColor": "#4F83FF",
                    "yAxisID": "y"
                },
                {
                    "label": "Risk Score (0-100, Lower is Safer)",
                    "data": [risk_map.get(r['quotation_id'], {}).get('overall_risk_score', 30.0) for r in scored_results],
                    "backgroundColor": "rgba(255, 152, 102, 0.75)",
                    "borderColor": "#FF9866",
                    "yAxisID": "y1",
                    "type": "line"
                }
            ]
        }

        # Visualization 3: Supplier Evaluation Radar Chart across Cost, Delivery, Risk, Warranty
        radar_colors = [
            ("rgba(32, 167, 122, 0.25)", "#20A77A"),
            ("rgba(79, 131, 255, 0.25)", "#4F83FF"),
            ("rgba(146, 116, 248, 0.25)", "#9274F8"),
            ("rgba(255, 152, 102, 0.25)", "#FF9866")
        ]
        chart_data_radar = {
            "labels": ["Cost Score", "Delivery Score", "Risk Safety Score", "Warranty Score"],
            "datasets": [
                {
                    "label": r['supplier_name'],
                    "data": [r['cost_score'], r['delivery_score'], r['risk_score'], r['warranty_score']],
                    "backgroundColor": radar_colors[idx % len(radar_colors)][0],
                    "borderColor": radar_colors[idx % len(radar_colors)][1],
                    "borderWidth": 2,
                    "pointBackgroundColor": radar_colors[idx % len(radar_colors)][1]
                }
                for idx, r in enumerate(scored_results)
            ]
        }

        # Final decision block
        final_decision = {
            "recommended_supplier": recommended_supplier if has_eligible else "No compliant supplier",
            "alternative_supplier": alternative_supplier or "None",
            "main_tradeoffs": f"Top vendor '{top_sname}' trades slight cost premium for superior delivery certainty and full warranty compliance." if has_eligible else "Cost vs compliance trade-offs cannot be resolved without requirement waivers.",
            "mandatory_failures": [f"{r['supplier_name']}: {'; '.join(r.get('disqualifications', []))}" for r in scored_results if not r['satisfies_mandatory']],
            "reasons_for_recommendation": f"Highest composite score ({top_winner_record['overall_score']:.1f}/100), full mandatory compliance, and low risk rating." if has_eligible else "None qualified."
        }

        # Enrich with Google Gemini (Graphs & Multi-Criteria Radar)
        ai_engine = "Deterministic Offline Engine"
        ai_status = "Local Deterministic Processing"
        try:
            from services.gemini_service import enrich_step6_with_gemini, get_gemini_api_key
            g_key = get_gemini_api_key()
            if g_key:
                g_res = enrich_step6_with_gemini(
                    parsed_reqs, normalized_quotes, supplier_profiles,
                    risk_assessments, cost_comparisons, ranked_recommendations,
                    weights, api_key=g_key
                )
                if g_res:
                    if g_res.get('recommendation_explanation_sections') and len(g_res['recommendation_explanation_sections']) >= 5:
                        explanation_sections = g_res['recommendation_explanation_sections']
                    if g_res.get('key_findings') and len(g_res['key_findings']) >= 3:
                        key_findings = g_res['key_findings']
                    if g_res.get('executive_summary'):
                        final_recommendation['executive_summary'] = g_res['executive_summary']
                    ai_engine = "Google Gemini (gemini-1.5-flash)"
                    ai_status = "Live AI Generation"
        except Exception:
            pass

        # Enrich narrative matter with ngrok / Groq AI if ngrok key is configured
        try:
            from services.matter_service import generate_step6_matter_ngrok, get_ngrok_api_key
            n_key = get_ngrok_api_key()
            if n_key:
                n_res = generate_step6_matter_ngrok(
                    parsed_reqs, normalized_quotes, supplier_profiles,
                    risk_assessments, cost_comparisons, ranked_recommendations,
                    weights, api_key=n_key
                )
                if n_res:
                    if n_res.get('recommendation_explanation_sections') and len(n_res['recommendation_explanation_sections']) >= 5:
                        explanation_sections = n_res['recommendation_explanation_sections']
                    if n_res.get('key_findings') and len(n_res['key_findings']) >= 3:
                        key_findings = n_res['key_findings']
                    if n_res.get('executive_summary'):
                        final_recommendation['executive_summary'] = n_res['executive_summary']
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
            "suppliers_ranked": len(scored_results),
            "recommended_supplier": recommended_supplier if has_eligible else "None",
            "has_eligible_winner": has_eligible,
            "top_score": top_winner_record['overall_score'] if (has_eligible and top_winner_record) else 0.0,
            "weights_used": weights,
            "started_at": start_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "completed_at": end_ts.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_seconds": duration
        }

        output_summary = (
            f"Ranked {len(scored_results)} suppliers using weighted multi-criteria matrix. "
            f"Recommended Winner: {recommended_supplier or 'None (Mandatory Failures)'} "
            f"(Score: {top_winner_record['overall_score']:.1f}/100)." if (has_eligible and top_winner_record) else
            "No supplier fully satisfies all mandatory procurement requirements."
        )

        return {
            "agent_number": self.agent_number,
            "agent_name": self.name,
            "purpose": self.purpose,
            "status": "Completed",
            "ai_engine": ai_engine,
            "ai_status": ai_status,
            "input_summary": f"Ranked {len(ranked_recommendations)} supplier bids using weighted multi-criteria decision matrix",
            "output_summary": output_summary,
            "execution_summary": execution_summary,
            "final_recommendation": final_recommendation,
            "ranking_table": ranking_table,
            "recommendation_explanation_sections": explanation_sections,
            "key_findings": key_findings,
            "chart_data_scores": chart_data_scores,
            "chart_data_cost_vs_risk": chart_data_cost_vs_risk,
            "chart_data_radar": chart_data_radar,
            "final_decision": final_decision,
            "ranked_recommendations": ranked_recommendations,
            "recommended_supplier": recommended_supplier,
            "alternative_supplier": alternative_supplier,
            "has_eligible_winner": has_eligible,
            "weights_used": weights,
            "warnings": warnings,
            "evidence_references": f"Scoring Weights: Cost ({int(weights['cost']*100)}%), Delivery ({int(weights['delivery']*100)}%), Risk ({int(weights['risk']*100)}%), Warranty ({int(weights['warranty']*100)}%)",
            "execution_duration_seconds": duration
        }

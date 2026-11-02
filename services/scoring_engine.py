"""
Transparent Vendor Scoring Engine for PROCUREMENTIQ AI
Normalizes multi-criteria procurement attributes (Cost, Delivery, Risk, Warranty),
enforces mandatory constraint gates, and produces explainable rankings.
"""

from datetime import datetime

DEFAULT_WEIGHTS = {
    'cost': 0.40,
    'delivery': 0.25,
    'risk': 0.20,
    'warranty': 0.15
}

def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    return None

def score_procurement_quotations(quotations, request_criteria, custom_weights=None):
    """
    Evaluates a list of quotation dicts/objects against a procurement request.
    
    quotations: list of dicts with keys:
      - id, supplier_name, total_cost, warranty_months, delivery_days, promised_delivery_date, risk_score
    request_criteria: dict with keys:
      - budget, required_delivery_date, min_warranty_months, created_at
    custom_weights: dict with 'cost', 'delivery', 'risk', 'warranty' (summing to 1.0)
    """
    if not quotations:
        return []

    weights = custom_weights or DEFAULT_WEIGHTS
    w_cost = float(weights.get('cost', 0.40))
    w_deliv = float(weights.get('delivery', 0.25))
    w_risk = float(weights.get('risk', 0.20))
    w_warr = float(weights.get('warranty', 0.15))
    
    # Normalize weights so they sum to 1.0
    total_w = w_cost + w_deliv + w_risk + w_warr
    if total_w > 0:
        w_cost /= total_w
        w_deliv /= total_w
        w_risk /= total_w
        w_warr /= total_w

    budget = float(request_criteria.get('budget', 0.0))
    req_deliv_date = parse_date(request_criteria.get('required_delivery_date'))
    min_warranty = int(request_criteria.get('min_warranty_months', 12))
    
    # Calculate baseline minimum cost among eligible quotations
    valid_costs = [q['total_cost'] for q in quotations if q.get('total_cost') and q['total_cost'] > 0]
    min_cost = min(valid_costs) if valid_costs else 1.0

    scored_list = []

    for q in quotations:
        cost = float(q.get('total_cost', 0.0))
        warranty = int(q.get('warranty_months') or 0)
        risk_score = float(q.get('risk_score', 30.0)) # 0 to 100, where 100 is maximum risk
        promised_date = parse_date(q.get('promised_delivery_date'))
        delivery_days = int(q.get('delivery_days') or 30)
        
        disqualifications = []
        
        # 1. Mandatory Constraint Checks
        if budget > 0 and cost > budget:
            disqualifications.append(f"Total cost (${cost:,.2f}) exceeds allocated budget (${budget:,.2f})")
            
        if min_warranty > 0 and warranty < min_warranty:
            disqualifications.append(f"Warranty duration ({warranty} months) fails mandatory minimum ({min_warranty} months)")
            
        if req_deliv_date and promised_date:
            if promised_date > req_deliv_date:
                days_over = (promised_date - req_deliv_date).days
                disqualifications.append(f"Promised delivery ({promised_date}) is {days_over} day(s) after requested deadline ({req_deliv_date})")

        satisfies_mandatory = len(disqualifications) == 0

        # 2. Cost Score (Lower total cost gets higher score)
        if cost > 0 and min_cost > 0:
            # Relative cost efficiency score: 100 * (min_cost / cost)
            cost_score = round(min(100.0, max(0.0, (min_cost / cost) * 100.0)), 1)
        else:
            cost_score = 50.0

        # 3. Delivery Score
        if req_deliv_date and promised_date:
            days_diff = (req_deliv_date - promised_date).days
            if days_diff >= 0:
                # Ahead of schedule: 80 base + up to 20 for early delivery
                delivery_score = round(min(100.0, 80.0 + (days_diff * 2.0)), 1)
            else:
                # Late: heavy penalty
                delivery_score = round(max(0.0, 70.0 + (days_diff * 10.0)), 1)
        else:
            # Fallback based on delivery days
            if delivery_days <= 14:
                delivery_score = 95.0
            elif delivery_days <= 30:
                delivery_score = 85.0
            elif delivery_days <= 60:
                delivery_score = 65.0
            else:
                delivery_score = 45.0

        # 4. Risk Score (Score = 100 - risk_score)
        # Low risk (e.g. 15) -> 85 score. High risk (e.g. 70) -> 30 score.
        normalized_risk_score = round(min(100.0, max(0.0, 100.0 - risk_score)), 1)

        # 5. Warranty Score
        if min_warranty > 0:
            if warranty >= min_warranty:
                # Base 85 + up to 15 bonus for extra warranty
                bonus = min(15.0, (warranty - min_warranty) * 2.5)
                warranty_score = round(min(100.0, 85.0 + bonus), 1)
            else:
                warranty_score = round(max(0.0, (warranty / min_warranty) * 60.0), 1)
        else:
            warranty_score = 80.0 if warranty >= 12 else 50.0

        # 6. Overall Weighted Score
        overall_score = round(
            (cost_score * w_cost) +
            (delivery_score * w_deliv) +
            (normalized_risk_score * w_risk) +
            (warranty_score * w_warr),
            1
        )

        weight_breakdown = {
            "cost_points": round(cost_score * w_cost, 1),
            "delivery_points": round(delivery_score * w_deliv, 1),
            "risk_points": round(normalized_risk_score * w_risk, 1),
            "warranty_points": round(warranty_score * w_warr, 1),
            "weights_used": {
                "cost": round(w_cost * 100),
                "delivery": round(w_deliv * 100),
                "risk": round(w_risk * 100),
                "warranty": round(w_warr * 100)
            }
        }

        scored_list.append({
            "quotation_id": q.get('id'),
            "supplier_name": q.get('supplier_name'),
            "total_cost": cost,
            "cost_score": cost_score,
            "delivery_score": delivery_score,
            "risk_score": normalized_risk_score,
            "warranty_score": warranty_score,
            "overall_score": overall_score,
            "weight_breakdown": weight_breakdown,
            "satisfies_mandatory": satisfies_mandatory,
            "disqualifications": disqualifications,
            "delivery_commitment": f"{delivery_days} days ({q.get('promised_delivery_date') or 'On schedule'})",
            "warranty_commitment": f"{warranty} months",
            "raw_risk": risk_score
        })

    # Ranking:
    # First priority: satisfies_mandatory == True
    # Second priority: overall_score descending
    scored_list.sort(key=lambda x: (1 if x['satisfies_mandatory'] else 0, x['overall_score']), reverse=True)

    has_eligible_winner = False
    for i, item in enumerate(scored_list, 1):
        item['rank'] = i
        if item['satisfies_mandatory'] and not has_eligible_winner:
            item['is_recommended'] = True
            has_eligible_winner = True
        else:
            item['is_recommended'] = False

    return scored_list

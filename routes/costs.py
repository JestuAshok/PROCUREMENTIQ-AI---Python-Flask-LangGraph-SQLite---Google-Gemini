"""
Cost Optimization and Landed Cost Breakdown Routes for PROCUREMENTIQ AI
Displays line-item cost comparisons, arithmetic formulas, freight/tax breakdowns, and charts.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for
from routes.auth import login_required
from database.db import query_db

costs_bp = Blueprint('costs', __name__)

@costs_bp.route('/cost-optimization')
@costs_bp.route('/costs')
@costs_bp.route('/cost-optimization/<int:request_id>')
@costs_bp.route('/costs/<int:request_id>')
@login_required
def cost_optimization(request_id=None):
    user_id = session.get('user_id')

    # Available requests
    available_requests = query_db("""
        SELECT r.id, r.request_code, r.item_name, r.budget, r.currency,
               (SELECT COUNT(*) FROM quotations q WHERE q.request_id = r.id) as quote_count
        FROM procurement_requests r
        WHERE r.user_id = ? OR r.user_id = 1
        ORDER BY r.id ASC
    """, (user_id,))

    # Default to request_id or the first request with quotes
    selected_request_id = request_id
    if not selected_request_id and available_requests:
        # Pick first one with quotes, or first overall
        req_with_quotes = next((r for r in available_requests if r['quote_count'] > 0), None)
        selected_request_id = req_with_quotes['id'] if req_with_quotes else available_requests[0]['id']

    selected_request = None
    cost_rows = []
    lowest_cost = 0.0
    highest_cost = 0.0
    cheapest_supplier = "None"
    chart_labels = []
    chart_subtotals = []
    chart_shipping = []
    chart_taxes = []
    chart_install = []
    chart_totals = []

    if selected_request_id:
        selected_request = query_db("SELECT * FROM procurement_requests WHERE id = ?", (selected_request_id,), one=True)
        cost_rows = query_db("""
            SELECT c.*, q.delivery_days, q.warranty_months, q.payment_terms,
                   COALESCE(rk.overall_risk_score, 30.0) as risk_score,
                   COALESCE(rk.risk_category, 'Medium Risk') as risk_category
            FROM cost_comparisons c
            JOIN quotations q ON c.quotation_id = q.id
            LEFT JOIN risk_assessments rk ON c.quotation_id = rk.quotation_id
            WHERE c.request_id = ?
            ORDER BY c.estimated_total_cost ASC
        """, (selected_request_id,))

        if cost_rows:
            costs = [c['estimated_total_cost'] for c in cost_rows]
            lowest_cost = min(costs)
            highest_cost = max(costs)
            cheapest_supplier = cost_rows[0]['supplier_name']

            for c in cost_rows:
                chart_labels.append(c['supplier_name'])
                chart_subtotals.append(c['net_subtotal'])
                chart_shipping.append(c['shipping_cost'])
                chart_taxes.append(c['tax_amount'])
                chart_install.append(c['installation_cost'] + c['other_charges'])
                chart_totals.append(c['estimated_total_cost'])

    return render_template(
        'cost_optimization.html',
        available_requests=available_requests,
        selected_request_id=selected_request_id,
        selected_request=selected_request,
        cost_rows=cost_rows,
        lowest_cost=lowest_cost,
        highest_cost=highest_cost,
        cheapest_supplier=cheapest_supplier,
        chart_data={
            "labels": chart_labels,
            "subtotals": chart_subtotals,
            "shipping": chart_shipping,
            "taxes": chart_taxes,
            "install": chart_install,
            "totals": chart_totals
        }
    )

"""
Dashboard and Landing routes for PROCUREMENTIQ AI
Renders the public landing page and the enterprise pastel dashboard.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from routes.auth import login_required
from database.db import query_db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def landing():
    is_logged_in = 'user_id' in session
    return render_template('landing.html', is_logged_in=is_logged_in)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    user_id = session.get('user_id')
    user_name = session.get('user_name', 'Jahnavi')

    # Fetch actual database KPI counts
    # 1. Total Requests
    tot_req_res = query_db(
        "SELECT COUNT(*) as cnt FROM procurement_requests WHERE user_id = ? OR ? = 1",
        (user_id, user_id), one=True
    )
    total_requests = tot_req_res['cnt'] if tot_req_res else 0

    # 2. Total Suppliers Analyzed
    tot_sup_res = query_db("SELECT COUNT(*) as cnt FROM suppliers", one=True)
    total_suppliers = tot_sup_res['cnt'] if tot_sup_res else 0

    # 3. Recommendations Ready
    recs_ready_res = query_db(
        "SELECT COUNT(*) as cnt FROM procurement_requests WHERE status = 'Recommendation Ready' AND (user_id = ? OR ? = 1)",
        (user_id, user_id), one=True
    )
    recs_ready = recs_ready_res['cnt'] if recs_ready_res else 0

    # 4. High Risk Suppliers
    high_risk_res = query_db(
        "SELECT COUNT(*) as cnt FROM suppliers WHERE compliance_status = 'High Risk' OR rating < 3.8",
        one=True
    )
    high_risk_count = high_risk_res['cnt'] if high_risk_res else 0

    # Ongoing Procurement Analysis table
    ongoing_requests = query_db("""
        SELECT r.id, r.request_code, r.item_name, r.category, r.status, r.updated_at,
               (SELECT COUNT(*) FROM quotations q WHERE q.request_id = r.id) as suppliers_count
        FROM procurement_requests r
        WHERE r.user_id = ? OR ? = 1
        ORDER BY r.id ASC
        LIMIT 5
    """, (user_id, user_id))

    # Top Vendor Recommendation Card (e.g. from PR-2026-001 or latest)
    top_recommendation = query_db("""
        SELECT rec.*, req.request_code, req.item_name
        FROM recommendations rec
        JOIN procurement_requests req ON rec.request_id = req.id
        WHERE rec.is_recommended = 1 AND (req.user_id = ? OR ? = 1)
        ORDER BY rec.id DESC
        LIMIT 1
    """, (user_id, user_id), one=True)

    # Cost Comparison Chart Data (for featured request, e.g. PR-2026-001)
    featured_quotes = query_db("""
        SELECT supplier_name, total_cost, currency
        FROM quotations
        WHERE request_id = 1
        ORDER BY id ASC
    """)
    cost_chart_labels = [q['supplier_name'].split()[0] + (" " + q['supplier_name'].split()[1] if len(q['supplier_name'].split()) > 1 else "") for q in featured_quotes] if featured_quotes else []
    cost_chart_values = [round(q['total_cost'] / 10000.0, 1) for q in featured_quotes] if featured_quotes else []

    # Risk Assessment Overview Donut Counts
    risk_low = query_db("SELECT COUNT(*) as cnt FROM suppliers WHERE rating >= 4.5", one=True)['cnt']
    risk_med = query_db("SELECT COUNT(*) as cnt FROM suppliers WHERE rating >= 4.0 AND rating < 4.5", one=True)['cnt']
    risk_high = query_db("SELECT COUNT(*) as cnt FROM suppliers WHERE rating < 4.0", one=True)['cnt']

    return render_template(
        'dashboard.html',
        user_name=user_name,
        total_requests=total_requests,
        total_suppliers=total_suppliers,
        recs_ready=recs_ready,
        high_risk_count=high_risk_count,
        ongoing_requests=ongoing_requests,
        top_recommendation=top_recommendation,
        cost_chart_labels=cost_chart_labels,
        cost_chart_values=cost_chart_values,
        risk_counts={
            "low": risk_low,
            "medium": risk_med,
            "high": risk_high,
            "total": risk_low + risk_med + risk_high
        }
    )

@dashboard_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return redirect(url_for('dashboard.dashboard_view'))

    user_id = session.get('user_id')
    results_requests = query_db("""
        SELECT id, request_code, item_name, category, status
        FROM procurement_requests
        WHERE (item_name LIKE ? OR request_code LIKE ? OR category LIKE ?)
          AND (user_id = ? OR user_id = 1)
    """, (f"%{q}%", f"%{q}%", f"%{q}%", user_id))

    results_suppliers = query_db("""
        SELECT id, name, code, category, tier, rating, compliance_status
        FROM suppliers
        WHERE name LIKE ? OR category LIKE ? OR country LIKE ?
    """, (f"%{q}%", f"%{q}%", f"%{q}%"))

    return render_template(
        'search_results.html',
        query=q,
        requests=results_requests,
        suppliers=results_suppliers
    )

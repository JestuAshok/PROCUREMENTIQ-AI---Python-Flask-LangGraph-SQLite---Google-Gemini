"""
Vendor Recommendations Routes for PROCUREMENTIQ AI
Renders ranked vendor shortlists, explainable trade-offs, side-by-side comparison, and human override logs.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from routes.auth import login_required
from database.db import query_db, execute_db

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommendations')
@recommendations_bp.route('/recommendations/<int:request_id>')
@login_required
def view_recommendations(request_id=None):
    user_id = session.get('user_id')

    available_requests = query_db("""
        SELECT r.id, r.request_code, r.item_name, r.budget, r.currency, r.status,
               (SELECT COUNT(*) FROM recommendations rec WHERE rec.request_id = r.id) as rec_count
        FROM procurement_requests r
        WHERE r.user_id = ? OR r.user_id = 1
        ORDER BY r.id ASC
    """, (user_id,))

    selected_request_id = request_id
    if not selected_request_id and available_requests:
        with_recs = next((r for r in available_requests if r['rec_count'] > 0), None)
        selected_request_id = with_recs['id'] if with_recs else available_requests[0]['id']

    selected_request = None
    recommendations_list = []
    top_recommended = None
    decision_history = []

    if selected_request_id:
        selected_request = query_db("SELECT * FROM procurement_requests WHERE id = ?", (selected_request_id,), one=True)
        recommendations_list = query_db("""
            SELECT rec.*, q.total_cost, q.unit_price, q.delivery_days, q.warranty_months,
                   q.payment_terms, q.quotation_number,
                   COALESCE(rk.risk_category, 'Low Risk') as risk_category,
                   COALESCE(rk.overall_risk_score, 20.0) as overall_risk_score,
                   COALESCE(rk.supporting_evidence, '') as supporting_evidence
            FROM recommendations rec
            JOIN quotations q ON rec.quotation_id = q.id
            LEFT JOIN risk_assessments rk ON rec.quotation_id = rk.quotation_id
            WHERE rec.request_id = ?
            ORDER BY rec.rank ASC
        """, (selected_request_id,))

        top_recommended = next((r for r in recommendations_list if r['is_recommended']), None)

        decision_history = query_db("""
            SELECT dh.*, u.full_name as user_name
            FROM decision_history dh
            JOIN users u ON dh.user_id = u.id
            WHERE dh.request_id = ?
            ORDER BY dh.id DESC
        """, (selected_request_id,))

    return render_template(
        'recommendations.html',
        available_requests=available_requests,
        selected_request_id=selected_request_id,
        selected_request=selected_request,
        recommendations=recommendations_list,
        top_recommended=top_recommended,
        decision_history=decision_history
    )

@recommendations_bp.route('/recommendations/<int:request_id>/override', methods=['POST'])
@login_required
def override_recommendation(request_id):
    user_id = session.get('user_id')
    selected_supplier = request.form.get('selected_supplier', '').strip()
    override_reason = request.form.get('override_reason', '').strip()
    recommended_supplier = request.form.get('recommended_supplier', '').strip()

    if not selected_supplier or not override_reason:
        flash("Both the selected supplier and a justification reason are required to log an override.", "danger")
        return redirect(url_for('recommendations.view_recommendations', request_id=request_id))

    was_overridden = 1 if selected_supplier.lower() != recommended_supplier.lower() else 0

    execute_db("""
        INSERT INTO decision_history (
            request_id, user_id, recommended_supplier, selected_supplier,
            was_overridden, override_reason
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (request_id, user_id, recommended_supplier, selected_supplier, was_overridden, override_reason))

    # Mark request as Completed
    execute_db("""
        UPDATE procurement_requests
        SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (request_id,))

    if was_overridden:
        flash(f"Manual override recorded: Selected '{selected_supplier}' over AI-recommended '{recommended_supplier}'. Decision logged.", "warning")
    else:
        flash(f"Confirmed procurement decision: Awarded to '{selected_supplier}'. Decision logged successfully.", "success")

    return redirect(url_for('recommendations.view_recommendations', request_id=request_id))

"""
Risk Assessment Routes for PROCUREMENTIQ AI
Displays transparent supplier risk scores, categories, delivery and compliance risks, and mitigations.
"""

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from routes.auth import login_required
from database.db import query_db

risks_bp = Blueprint('risks', __name__)

@risks_bp.route('/risks')
@login_required
def list_risks():
    category_filter = request.args.get('category', '').strip()
    request_filter = request.args.get('request_id', '').strip()

    sql = """
        SELECT rk.*, r.request_code, r.item_name, r.id as req_id,
               s.rating as supplier_rating, s.tier, s.on_time_delivery_rate
        FROM risk_assessments rk
        JOIN procurement_requests r ON rk.request_id = r.id
        LEFT JOIN suppliers s ON rk.supplier_name LIKE s.name
        WHERE 1=1
    """
    params = []

    if category_filter:
        if category_filter == 'Low Risk':
            sql += " AND (rk.risk_category = 'Low Risk' OR (rk.overall_risk_score IS NOT NULL AND rk.overall_risk_score <= 25))"
        elif category_filter == 'Medium Risk':
            sql += " AND (rk.risk_category = 'Medium Risk' OR (rk.overall_risk_score IS NOT NULL AND rk.overall_risk_score > 25 AND rk.overall_risk_score <= 55))"
        elif category_filter == 'High Risk':
            sql += " AND (rk.risk_category = 'High Risk' OR (rk.overall_risk_score IS NOT NULL AND rk.overall_risk_score > 55))"
        elif category_filter == 'Insufficient Data':
            sql += " AND (rk.risk_category = 'Insufficient Data' OR rk.risk_category LIKE '%Pending%' OR rk.risk_category LIKE '%Insufficient%')"
        else:
            sql += " AND rk.risk_category = ?"
            params.append(category_filter)
    if request_filter:
        sql += " AND rk.request_id = ?"
        params.append(request_filter)

    sql += " ORDER BY rk.overall_risk_score DESC, rk.id DESC"
    risk_records = query_db(sql, params)

    # Risk category summary counts
    all_risks = query_db("SELECT risk_category, overall_risk_score FROM risk_assessments")
    low_cnt = sum(1 for r in all_risks if r['risk_category'] == 'Low Risk' or (r['overall_risk_score'] and r['overall_risk_score'] <= 25))
    med_cnt = sum(1 for r in all_risks if (r['risk_category'] == 'Medium Risk' or (r['overall_risk_score'] and 25 < r['overall_risk_score'] <= 55)) and not (r['overall_risk_score'] and r['overall_risk_score'] > 55) and not (r['overall_risk_score'] and r['overall_risk_score'] <= 25))
    high_cnt = sum(1 for r in all_risks if r['risk_category'] == 'High Risk' or (r['overall_risk_score'] and r['overall_risk_score'] > 55))
    ins_cnt = sum(1 for r in all_risks if ('Pending' in (r['risk_category'] or '') or 'Insufficient' in (r['risk_category'] or '')) and not (r['overall_risk_score'] and r['overall_risk_score'] > 55))

    # Available requests for filter
    available_requests = query_db("SELECT DISTINCT id, request_code, item_name FROM procurement_requests ORDER BY id ASC")

    return render_template(
        'risks.html',
        risk_records=risk_records,
        category_filter=category_filter,
        request_filter=request_filter,
        available_requests=available_requests,
        counts={
            "low": low_cnt,
            "medium": med_cnt,
            "high": high_cnt,
            "insufficient": ins_cnt,
            "total": len(all_risks)
        }
    )

@risks_bp.route('/risks/<int:risk_id>')
@login_required
def risk_detail(risk_id):
    risk = query_db("""
        SELECT rk.*, r.request_code, r.item_name, r.budget, r.required_delivery_date,
               q.quotation_number, q.delivery_days, q.warranty_months, q.payment_terms,
               s.country, s.tier, s.rating as supplier_rating, s.compliance_status as reg_status
        FROM risk_assessments rk
        JOIN procurement_requests r ON rk.request_id = r.id
        JOIN quotations q ON rk.quotation_id = q.id
        LEFT JOIN suppliers s ON rk.supplier_name LIKE s.name
        WHERE rk.id = ?
    """, (risk_id,), one=True)

    if not risk:
        flash("Risk assessment record not found.", "danger")
        return redirect(url_for('risks.list_risks'))

    return render_template('risk_detail.html', risk=risk)

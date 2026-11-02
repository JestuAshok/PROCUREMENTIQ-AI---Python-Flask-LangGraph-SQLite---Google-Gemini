"""
Quotation Review and Analysis Routes for PROCUREMENTIQ AI
Allows human-in-the-loop inspection, editing, and confirmation of extracted quotation fields.
"""

import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth import login_required
from database.db import query_db, execute_db
from services.cost_calculator import calculate_quotation_cost

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/<int:request_id>')
@login_required
def review_quotations(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    quotations = query_db("""
        SELECT q.*, s.tier, s.rating as supplier_rating, s.compliance_status
        FROM quotations q
        LEFT JOIN suppliers s ON q.supplier_id = s.id
        WHERE q.request_id = ?
        ORDER BY q.id ASC
    """, (request_id,))

    # Parse JSON missing_fields for each quote
    quotes_list = []
    for q in quotations:
        q_dict = dict(q)
        mf = q_dict.get('missing_fields')
        if isinstance(mf, str):
            try:
                q_dict['missing_list'] = json.loads(mf)
            except Exception:
                q_dict['missing_list'] = [mf] if mf else []
        else:
            q_dict['missing_list'] = mf or []
        quotes_list.append(q_dict)

    return render_template(
        'quotation_analysis.html',
        proc_req=req,
        quotations=quotes_list
    )

@analysis_bp.route('/analysis/<int:request_id>/update-quote/<int:quote_id>', methods=['POST'])
@login_required
def update_quote(request_id, quote_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR user_id = 1)",
        (request_id, user_id), one=True
    )
    if not req:
        flash("Request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    supplier_name = request.form.get('supplier_name', '').strip()
    quotation_number = request.form.get('quotation_number', '').strip()
    unit_price = float(request.form.get('unit_price') or 0.0)
    quantity = int(request.form.get('quantity') or 1)
    currency = request.form.get('currency', 'USD').strip()
    discount_amount = float(request.form.get('discount_amount') or 0.0)
    tax_rate = float(request.form.get('tax_rate') or 0.0)
    shipping_cost = float(request.form.get('shipping_cost') or 0.0)
    installation_cost = float(request.form.get('installation_cost') or 0.0)
    other_charges = float(request.form.get('other_charges') or 0.0)
    warranty_months = int(request.form.get('warranty_months') or 12)
    delivery_days = int(request.form.get('delivery_days') or 30)
    promised_delivery_date = request.form.get('promised_delivery_date', '').strip()
    payment_terms = request.form.get('payment_terms', 'Net 30').strip()
    quote_validity_date = request.form.get('quote_validity_date', '').strip()

    # Recalculate deterministic total cost
    c_res = calculate_quotation_cost(
        unit_price=unit_price,
        quantity=quantity,
        discount_amount=discount_amount,
        tax_rate=tax_rate,
        shipping_cost=shipping_cost,
        installation_cost=installation_cost,
        other_charges=other_charges,
        currency=currency
    )

    execute_db("""
        UPDATE quotations
        SET supplier_name = ?, quotation_number = ?, unit_price = ?, quantity = ?,
            currency = ?, discount_amount = ?, tax_rate = ?, tax_amount = ?,
            shipping_cost = ?, installation_cost = ?, other_charges = ?,
            total_cost = ?, warranty_months = ?, delivery_days = ?,
            promised_delivery_date = ?, payment_terms = ?, quote_validity_date = ?,
            is_confirmed = 1, missing_fields = '[]', extraction_confidence = 100.0
        WHERE id = ? AND request_id = ?
    """, (
        supplier_name, quotation_number, unit_price, quantity,
        currency, discount_amount, tax_rate, c_res['tax_amount'],
        shipping_cost, installation_cost, other_charges,
        c_res['estimated_total_cost'], warranty_months, delivery_days,
        promised_delivery_date, payment_terms, quote_validity_date,
        quote_id, request_id
    ))

    flash(f"Quotation from '{supplier_name}' confirmed and updated successfully!", "success")
    return redirect(url_for('analysis.review_quotations', request_id=request_id))

@analysis_bp.route('/analysis/<int:request_id>/delete-quote/<int:quote_id>', methods=['POST'])
@login_required
def delete_quote(request_id, quote_id):
    execute_db("DELETE FROM quotations WHERE id = ? AND request_id = ?", (quote_id, request_id))
    flash("Quotation removed successfully.", "info")
    return redirect(url_for('analysis.review_quotations', request_id=request_id))
